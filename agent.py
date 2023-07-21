import torch
import random
import numpy as np
from collections import deque
from flappy_game import FlappyGame
from model import Linear_QNet, QTrainer
from helper import plot

MAX_MEMORY = 100_000
BATCH_SIZE = 1000
LR = 0.001


class Agent:

    def __init__(self):
        self.n_games = 0
        self.epsilon = 0  # randomness
        self.gamma = 0.9  # discount rate
        self.memory = deque(maxlen=MAX_MEMORY)  # popleft()
        # 此处构建一个模型
        # 将有11个输入节点 通过 256个隐藏层 转成我们能进行的 2个操作
        # 对应一共11个输入状态的值分别是
        # 2个输出层 （飞or不飞）
        self.model = Linear_QNet(3, 6, 2)
        self.trainer = QTrainer(self.model, lr=LR, gamma=self.gamma)

    def get_state(self, game):

        state = [
            # 这里要建模
            # 需要知道离地面高度
            # game.getPlayerY(),
            # 与下一柱子的左边沿的deltaX
            game.getNextPillarDis(),
            # 与下一柱子的左边沿的deltaY
            game.getNextPillarCenterY(),
            # 当前的vy
            game.getPlayerVy()
        ]

        return np.array(state, dtype=float)

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))  # popleft if MAX_MEMORY is reached

    def train_long_memory(self):
        if len(self.memory) > BATCH_SIZE:
            mini_sample = random.sample(self.memory, BATCH_SIZE)  # list of tuples
        else:
            mini_sample = self.memory

        states, actions, rewards, next_states, dones = zip(*mini_sample)
        self.trainer.train_step(states, actions, rewards, next_states, dones)
        # for state, action, reward, nexrt_state, done in mini_sample:
        #    self.trainer.train_step(state, action, reward, next_state, done)

    def train_short_memory(self, state, action, reward, next_state, done):
        self.trainer.train_step(state, action, reward, next_state, done)

    def get_action(self, state):
        # random moves: tradeoff exploration / exploitation
        self.epsilon = 0 - self.n_games
        final_move = [0, 0]
        if random.randint(0, 200) < self.epsilon:
            move = random.randint(1, 20)  # 在飞和不飞之间选一个
            if move == 1:
                final_move[1] = 1
            else:
                final_move[0] = 1
        else:
            state0 = torch.tensor(state, dtype=torch.float)
            prediction = self.model(state0)
            move = torch.argmax(prediction).item()  # 运用模型去预测现在是非还是不飞
            final_move[move] = 1

        return final_move


def train():
    plot_scores = []
    plot_mean_scores = []
    total_score = 0
    record = 0
    agent = Agent()
    game = FlappyGame()
    game.start()


    while True:
        # get old state
        state_old = agent.get_state(game)
        # print(state_old)
        # get move
        final_move = agent.get_action(state_old)


        # perform move and get new state
        reward, done, score, crashInfo = game.play_step(final_move)
        state_new = agent.get_state(game)

        # train short memory
        agent.train_short_memory(state_old, final_move, reward, state_new, done)

        # remember
        agent.remember(state_old, final_move, reward, state_new, done)

        if done:
            # train long memory, plot result
            game.reset()
            # game.showGameOverScreen(crashInfo)
            agent.n_games += 1
            agent.train_long_memory()

            if score > record:
                record = score
                agent.model.save()

            print('Game', agent.n_games, 'Score', score, 'Record:', record)

            plot_scores.append(score)
            total_score += score
            mean_score = total_score / agent.n_games
            plot_mean_scores.append(mean_score)
            plot(plot_scores, plot_mean_scores)


if __name__ == '__main__':
    train()