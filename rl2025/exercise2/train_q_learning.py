import gymnasium as gym
from tqdm import tqdm

from rl2025.constants import EX2_QL_CONSTANTS as CONSTANTS
from rl2025.exercise2.agents import QLearningAgent
from rl2025.exercise2.utils import evaluate

CONFIG = {
    "eval_freq": 1000, # keep this unchanged
    "alpha": 0.05,
    "epsilon": 0.9,
    "gamma": 0.99,
}
CONFIG.update(CONSTANTS)


def q_learning_eval(
        env,
        config,
        q_table,
        render=False):
    """
    Evaluate configuration of Q-learning on given environment when initialised with given Q-table

    :param env (gym.Env): environment to execute evaluation on
    :param config (Dict[str, float]): configuration dictionary containing hyperparameters
    :param q_table (Dict[(Obs, Act), float]): Q-table mapping observation-action to Q-values
    :param render (bool): flag whether evaluation runs should be rendered
    :return (float, float): mean and standard deviation of returns received over episodes
    """
    eval_agent = QLearningAgent(
        action_space=env.action_space,
        obs_space=env.observation_space,
        gamma=config["gamma"],
        alpha=config["alpha"],
        epsilon=0.0,
    )
    eval_agent.q_table = q_table
    if render:
        eval_env = gym.make(CONFIG["env"], render_mode="human")
    else:
        eval_env = env
    return evaluate(eval_env, eval_agent, config["eval_eps_max_steps"], config["eval_episodes"])


def train(env, config):
    """
    Train and evaluate Q-Learning on given environment with provided hyperparameters

    :param env (gym.Env): environment to execute evaluation on
    :param config (Dict[str, float]): configuration dictionary containing hyperparameters
    :return (float, List[float], List[float], Dict[(Obs, Act), float]):
        total reward over all episodes, list of means and standard deviations of evaluation
        returns, final Q-table
    """
    agent = QLearningAgent(
        action_space=env.action_space,
        obs_space=env.observation_space,
        gamma=config["gamma"],
        alpha=config["alpha"],
        epsilon=config["epsilon"],
    )

    step_counter = 0
    max_steps = config["total_eps"] * config["eps_max_steps"]

    total_reward = 0
    evaluation_return_means = []
    evaluation_negative_returns = []

    for eps_num in tqdm(range(1, config["total_eps"]+1)):
        obs, _ = env.reset()
        episodic_return = 0
        t = 0

        while t < config["eps_max_steps"]:
            agent.schedule_hyperparameters(step_counter, max_steps)
            act = agent.act(obs)
            n_obs, reward, terminated, truncated, _ = env.step(act)
            done = terminated or truncated
            agent.learn(obs, act, reward, n_obs, done)

            t += 1
            step_counter += 1
            episodic_return += reward

            if done:
                break

            obs = n_obs

        total_reward += episodic_return

        if eps_num > 0 and eps_num % config["eval_freq"] == 0:
            mean_return, negative_returns = q_learning_eval(env, config, agent.q_table)
            tqdm.write(f"EVALUATION: EP {eps_num} - MEAN RETURN {mean_return}")
            evaluation_return_means.append(mean_return)
            evaluation_negative_returns.append(negative_returns)

    return total_reward, evaluation_return_means, evaluation_negative_returns, agent.q_table


if __name__ == "__main__":
    SWEEP = True
    is_slippery= False
    if SWEEP:
        import json
        eval_return_mean = {}
        for i in range(10):
            print(f'Sweep:  {i+1}/10')
            env = gym.make(CONFIG["env"], is_slippery=is_slippery)
            _, eval_return, _, _ = train(env, CONFIG)
            max_eval = max(eval_return) if eval_return else 0
            eval_return_mean[str(i)] = max_eval

            overall_mean = sum(eval_return_mean.values())/len(eval_return_mean)
            result_data = {
                "results": eval_return_mean,
                "mean": overall_mean
            }
        
        gamma = CONFIG["gamma"]
        filepath = f"rl2025/exercise2/results/q_learning_sweep_results_{gamma}_is_slippery_{is_slippery}.json"
        with open(filepath, "w") as f:
            json.dump(result_data, f, indent=4)

        print(filepath)

    else:    
        env = gym.make(CONFIG["env"], is_slippery=is_slippery)
        total_reward, _, _, q_table = train(env, CONFIG)
