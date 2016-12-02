import sys
import copy
import random
import math

RMS_bound = [
    1.000,  # 1
    0.828,
    0.780,
    0.757,
    0.743,
    0.735,
    0.729,
    0.724,
    0.721,
    0.718,  # 10
    0.715,
    0.713,
    0.712,
    0.711,
    0.710,
    0.708,
    0.707,
    0.707,
    0.706,
    0.693,  # >=20
]

SCALE_SYS_FREQ = [
    51000,
    102000,
    204000,
    340000,
    475000,
    640000,
    760000,
    860000,
    1000000,
    1100000,
    1200000,
    1300000,
]

MAX_SYSCLOCK_FREQ = 1300000
MIN_SYSCLOCK_FREQ = 51000


class System:
    def __init__(self):
        self.cpu = dict()
        for i in range(4):
            self.cpu[i] = []

    def insert(self, cpuid, task):
        self.cpu[cpuid].append(task)
        sorted(self.cpu[cpuid], reverse=True)

    def tasks(self, cpuid):
        return copy.deepcopy(self.cpu[cpuid])

    def util_all(self):
        return [sum([(task.c / task.t) for task in tasks]) for cpuid, tasks in self.cpu.items()]

    def util(self, cpuid):
        return sum([(task.c / task.t) for task in self.cpu[cpuid]])

    def rank(self):
        infos = [(sum([(task.c / task.t) for task in tasks]), cpuid) for cpuid, tasks in self.cpu.items()]
        return [info[1] for info in sorted(infos, key=lambda tup: tup[0], reverse=False)]

    def info(self):
        for cpuid, tasks in self.cpu.items():
            print('CPU{:d}: {}'.format(cpuid, ', '.join([str(task) for task in tasks])))

    def check_schedulable(self, cpuid, new_task):
        tasks = self.cpu[cpuid]
        C = new_task.c
        T = new_task.t
        util = 0
        for task in tasks:
            util += float(task.c) / task.t
        util += float(C) / T
        rms_bound = RMS_bound[len(tasks) - 1]
        if util > rms_bound:
            return False

        i = 0
        for task in tasks:
            if T < task.t:
                break
            i += 1

        new_tasks = copy.deepcopy(tasks)
        new_tasks.insert(i, new_task)
        task_num = len(new_tasks)

        a_k = 0
        a_k1 = 0
        for i in range(0, task_num):
            a_0 = 0
            util = 0
            for j in range(0, i + 1):
                util += float(new_tasks[j].c) / new_tasks[j].t

            # check if it exceeds 1.0
            if util > RMS_bound[0]:
                return False

            # if util is within the bound, continue the next task
            if util <= RMS_bound[i]:
                continue

            for j in range(0, i + 1):
                a_0 += new_tasks[j].c

            if a_0 > new_tasks[i].t:
                return False

            for j in range(0, i + 1):
                tmp = 0
                if j == 0:
                    a_k = a_0
                for k in range(0, i):
                    tmp += math.ceil(float(a_k) / new_tasks[k].t) * new_tasks[k].c

                a_k1 = tmp + new_tasks[i].c

                if a_k1 > new_tasks[i].t:
                    return False

                if i != 0 and a_k == a_k1:
                    if a_k <= new_tasks[i].t:
                        break
                    else:
                        return False
                a_k = a_k1
        return True

    def generate_sysclock_percpu(self, cpuid):
        tasks = self.cpu[cpuid]
        final_freq = 0.0
        task_num = len(tasks)
        if task_num == 0:
            return MAX_SYSCLOCK_FREQ

        # init the freq list
        freq_list = []
        for i in range(0, task_num):
            freq_list.append(1.0)

        for i in range(0, task_num):
            period = tasks[i].t
            for j in range(0, i + 1):
                p = tasks[j].c
                for k in range(1, task_num):
                    t = k * p
                    tmp = 0
                    if t > period:
                        break
                    for l in range(0, i + 1):
                        tmp += math.ceil(float(t) / tasks[l].t) * tasks[l].c

                    util = float(tmp) / t
                    if util < freq_list[i]:
                        freq_list[i] = util

        for i in range(0, task_num):
            if freq_list[i] > final_freq:
                final_freq = freq_list[i]
        return final_freq * MAX_SYSCLOCK_FREQ

    def generate_sysclock(self):
        final_sysclock = 0

        for cpuid in range(0, 4):
            tmp = self.generate_sysclock_percpu(cpuid)
            if tmp > final_sysclock:
                final_sysclock = tmp

        return final_sysclock


class Task:
    def __init__(self, c=0, t=1000):
        self.c = c
        self.t = t

    def __gt__(self, task2):
        return float(self.c) / self.t > float(task2.c) / task2.t

    def __str__(self):
        return '({:.1f}, {:.1f})'.format(self.c, self.t)


if __name__ == '__main__':

    if len(sys.argv) < 2:
        sys.exit(1)

    tasks = []
    policy = sys.argv[1]
    for i in range(5):
        ran = abs(random.gauss(0.2, 0.1))
        period = random.uniform(500, 1500)
        tasks.append(Task(period * ran, period))

    rt = System()
    """
    for task in tasks:
        rt.insert(0, task)
    
    for i in range(1, 4):
        rt.insert(2, Task(random.uniform(1, 5), 5))
    """
    for task in tasks:
        order = rt.rank()
        offline = [cpu for cpu in order if rt.util(cpu) == 0]

        print(str(float(task.c)/task.t))
        print(order)
        print([rt.util(cpu) for cpu in order])

        if policy == 'WF':
            online = [cpu for cpu in order if rt.util(cpu) != 0].reverse()
            if not online:
                online = order
        elif policy == 'BF':
            online = order
        else:
            online = order.reverse()

        print("Online: " + str(online))
        for cpuid in online:
            if rt.check_schedulable(cpuid, task):
                print ("Insert task: {} to cpu: {:d}".format(str(task), cpuid))
                rt.insert(cpuid, task)
                continue

        if offline:
            print("Turn on offline cpu {:d}".format(offline[0]))
            rt.insert(offline[0], task)
        else:
            print('Unable to schechule on any cpu')
            sys.exit(1)

    print(rt.rank())
    rt.info()