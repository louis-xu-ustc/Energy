import copy
import math
import System
import Task

RMS_bound = [
    1.000, #1
    0.828,
    0.780,
    0.757,
    0.743,
    0.735,
    0.729,
    0.724,
    0.721,
    0.718, #10
    0.715,
    0.713,
    0.712,
    0.711,
    0.710,
    0.708,
    0.707,
    0.707,
    0.706,
    0.693, # >=20
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


def check_one_processor_scheduabililty(cpuid, C, T, task_list):
    util = 0
    for task in task_list:
        util += float(task.c)/task.t
    util += float(C)/T
    rms_bound = RMS_bound[len(task_list)-1]
    if util > rms_bound:
        return -1

    i = 0
    for task in task_list:
        if T < task.t:
            break
        i += 1

    new_task_list = copy.deepcopy(task_list)
    new_task = Task(C, T)
    new_task_list.insert(i, new_task)
    task_num = len(new_task_list)


    a_k = 0
    a_k1 = 0
    for i in range(0, task_num):
        a_0 = 0
        util = 0
        for j in range(0, i+1):
            util += float(new_task_list[j].c)/new_task_list[j].t

        # check if it exceeds 1.0
        if util > RMS_bound[0]:
            return -1

        # if util is within the bound, continue the next task
        if util <= RMS_bound[i]:
            continue

        for j in range(0, i+1):
            a_0 += new_task_list[j].c

        if a_0 > new_task_list[i].t:
            return -1

        for j in range(0, i+1):
            tmp = 0
            if j == 0:
                a_k = a_0
            for k in range(0, i):
                tmp += math.ceil(float(a_k)/new_task_list[k].t) * new_task_list[k].c

            a_k1 = tmp + new_task_list[i].c

            if a_k1 > new_task_list[i].t:
                return -1

            if i != 0 and a_k == a_k1:
                if a_k <= new_task_list[i].t:
                    break
                else:
                    return -1
            a_k = a_k1

    return 0



def generate_sysclock_percpu(cpuid, task_list):
    final_freq = 0.0
    task_num = len(task_list)
    if task_num == 0:
        return MAX_SYSCLOCK_FREQ

    # init the freq list
    freq_list = []
    for i in range(0, task_num):
        freq_list.append(1.0)

    for i in range(0, task_num):
        period = task_list[i].t
        for j in range(0, i+1):
            p = task_list[j].c
            for k in range(1, task_num):
                t = k * p
                tmp = 0
                if t > period:
                    break
                for l in range(0, i+1):
                    tmp += math.ceil(float(t)/task_list[l].t) * task_list[l].c

                util = float(tmp)/t
                if util < freq_list[i]:
                    freq_list[i] = util

    for i in range(0, task_num):
        if freq_list[i] > final_freq:
            final_freq =freq_list[i]
    return final_freq * MAX_SYSCLOCK_FREQ


def generate_sysclock():
    final_sysclock = 0

    for cpuid in range(0, 4):
        tmp = generate_sysclock_percpu(cpuid, System.get_tasks(cpuid))
        if tmp > final_sysclock:
            final_sysclock = tmp

    return final_sysclock










