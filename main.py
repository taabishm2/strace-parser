import re
import csv
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd
import math
import os


def get_fields(syscall):
    syscall = syscall.replace("\n", "")
    res = syscall.split(" ")
    return res[0], res[1], res[-2], res[-1]


def parse_call(syscall, fn_name):
    pid, timestamp, ret_val, duration = get_fields(syscall)
    fn_args_list = get_fn_arguments(syscall, fn_name)
    return [pid, timestamp, ret_val, duration] + fn_args_list


def get_fn_arguments(syscall, fn_name):
    pattern = re.compile("(?<=" + fn_name + "\().*(?=\))")
    fn_args_str = pattern.findall(syscall)[0]
    fn_args_list = [i.strip() for i in fn_args_str.split(",")]
    return fn_args_list


def get_fields_for_unfinished(syscall):
    syscall = syscall.replace("\n", "")
    res = syscall.split(" ")
    return res[0], res[1]


def parse_call_for_unfinished(syscall, fn_name):
    pid, timestamp = get_fields_for_unfinished(syscall)
    fn_args_list = get_fn_arguments_for_unfinished(syscall, fn_name)
    return [pid, timestamp] + fn_args_list


def get_fn_arguments_for_unfinished(syscall, fn_name):
    pattern = re.compile("(?<=" + fn_name + "\().*(?=\<)")
    fn_args_str = pattern.findall(syscall)[0]
    fn_args_list = [i.strip() for i in fn_args_str.split(",")]
    return fn_args_list


def get_fields_for_resumed(syscall):
    syscall = syscall.replace("\n", "")
    res = syscall.split(" ")
    return res[0], res[-2], res[-1]


def draw_mem_boxplot(trace_name):
    mmap_file = open('results/mmap.csv')
    munmap_file = open('results/munmap.csv')
    brk_file = open('results/brk.csv')

    mmap_reader = csv.reader(mmap_file)
    munmap_reader = csv.reader(munmap_file)
    brk_reader = csv.reader(brk_file)
    next(mmap_reader)
    next(munmap_reader)
    next(brk_reader)

    mmaps, munmps, brks, top_addr_map = [], [], [], dict()
    for row in mmap_reader:
        mmaps.append(int(row[5]))
    for row in munmap_reader:
        munmps.append(int(row[5]))
    for row in brk_reader:
        if row[0] not in top_addr_map: top_addr_map[row[0]] = row[2]
        if row[4] == "NULL": continue
        top_addr, new_top = top_addr_map[row[0]], row[4]
        memory_diff = int(new_top, 16) - int(top_addr, 16)
        brks.append(memory_diff)
        top_addr_map[row[0]] = row[2]

    data_dict = {'mmap':mmaps, 'munmap':munmps, 'brk':brks}

    plt.clf()

    plt.boxplot(data_dict.values(), vert=True, patch_artist=True, labels=data_dict.keys(), showfliers=True)

    plt.ylabel("Memory (bytes)")
    plt.title(trace_name)
    # bplot1 = ax1.boxplot(all_data,
    #                      vert=True,  # vertical box alignment
    #                      patch_artist=True,  # fill with color
    #                      labels=labels)  # will be used to label x-ticks
    # ax1.set_title('Rectangular box plot')
    #
    # merged_values.sort(key=lambda x: x[0])
    # start_time = merged_values[0][0]
    # for i in merged_values:
    #     i[0] = (i[0] - start_time).total_seconds()
    #
    # for i in range(1, len(merged_values)):
    #     merged_values[i][1] += merged_values[i - 1][1]
    #
    # plt.plot([x[0] for x in merged_values], [x[1] for x in merged_values], label=trace_name)
    # plt.title('Memory consumed timeline')
    # plt.legend(loc='lower right')
    # plt.xlabel("Time elapsed (sec)")
    # plt.ylabel("Memory used (bytes)")
    plt.savefig('graphs/' + trace_name + '-memusebox')
def draw_line_chart_mem_use(trace_name):
    mmap_file = open('results/mmap.csv')
    munmap_file = open('results/munmap.csv')
    brk_file = open('results/brk.csv')

    mmap_reader = csv.reader(mmap_file)
    munmap_reader = csv.reader(munmap_file)
    brk_reader = csv.reader(brk_file)
    next(mmap_reader)
    next(munmap_reader)
    next(brk_reader)

    merged_values, top_addr_map = [], dict()
    for row in mmap_reader:
        merged_values.append([datetime.strptime(str(row[1]), '%H:%M:%S.%f'), int(row[5])])
    for row in munmap_reader:
        merged_values.append([datetime.strptime(str(row[1]), '%H:%M:%S.%f'), -int(row[5])])
    for row in brk_reader:
        if row[0] not in top_addr_map: top_addr_map[row[0]] = row[2]
        if row[4] == "NULL": continue
        top_addr, new_top = top_addr_map[row[0]], row[4]
        memory_diff = int(new_top, 16) - int(top_addr, 16)
        merged_values.append([datetime.strptime(str(row[1]), '%H:%M:%S.%f'), memory_diff])
        top_addr_map[row[0]] = row[2]

    merged_values.sort(key=lambda x: x[0])
    start_time = merged_values[0][0]
    for i in merged_values:
        i[0] = (i[0] - start_time).total_seconds()

    for i in range(1, len(merged_values)):
        merged_values[i][1] += merged_values[i - 1][1]

    plt.plot([x[0] for x in merged_values], [x[1] for x in merged_values], label=trace_name)
    plt.title('Memory consumed timeline')
    plt.legend(loc='lower right')
    plt.xlabel("Time elapsed (sec)")
    plt.ylabel("Memory used (bytes)")
    plt.savefig('graphs/' + trace_name + '-memuse')

def draw_bar_chart_mem_lifespan_without_bin(trace_name):
    mmap_file = open('results/mmap.csv')
    munmap_file = open('results/munmap.csv')

    mmap_reader = csv.reader(mmap_file)
    munmap_reader = csv.reader(munmap_file)
    next(mmap_reader)
    next(munmap_reader)
    
    mmap_dict = dict()
    for row in mmap_reader:
        if row[2] == "MAP_FAILED":
            continue
        key = (row[2], row[5])
        if key not in mmap_dict:
            mmap_dict[key] = []
        mmap_dict[key].append(datetime.strptime(str(row[1]), '%H:%M:%S.%f'))

    munmap_dict = dict()
    for row in munmap_reader:
        if row[2] == "-1":
            continue 
        key = (row[4], row[5])
        if key not in munmap_dict:
            munmap_dict[key] = []
        munmap_dict[key].append(datetime.strptime(str(row[1]), '%H:%M:%S.%f'))

    plot_values = []
    for key in mmap_dict:
        if key in munmap_dict:
            mmap_list = mmap_dict[key]
            mmap_list.sort()
            munmap_list = munmap_dict[key]
            munmap_list.sort()
            mmap_size = len(mmap_list)
            munmap_size = len(munmap_list)
            for index in range(mmap_size):
                if index >= munmap_size:
                    break
                delta = munmap_dict[key][index] - mmap_dict[key][index]
                epoch = datetime(1900, 1, 1)
                time_passed = mmap_dict[key][index] - epoch
                time_in_seconds = delta.total_seconds()
                if time_in_seconds < 0.0:
                    time_in_seconds = -1 * time_in_seconds
                plot_values.append([(key[0], time_passed.total_seconds()), time_in_seconds])            
    plot_values.sort()
    plt.clf()
    plt.rc('axes', titlesize=80)
    plt.rc('axes', labelsize=75)
    plt.rc('xtick', labelsize=15)
    plt.rc('ytick', labelsize=40)
    fig = plt.figure(figsize=(100,100), tight_layout = True)                          
    plt.bar([i+1 for i in range(len(plot_values))], [math.log(x[1]*1000000,10) for x in plot_values])
    plt.xticks([i+1 for i in range(len(plot_values))][::20], [x[0] for x in plot_values][::20], rotation = 75)
    plt.xlim(1,len(plot_values)+1)
    plt.title("Lifespan of allocations")
    plt.xlabel("Virtual Address")
    plt.ylabel("Lifespan in log(microsecs)")
    fig.align_labels()
    plt.savefig("graphs/" + trace_name + "-lifespan", dpi = 150)

def draw_bar_chart_mem_lifespan_with_bin(trace_name):
    mmap_file = open('results/mmap.csv')
    munmap_file = open('results/munmap.csv')

    mmap_reader = csv.reader(mmap_file)
    munmap_reader = csv.reader(munmap_file)
    next(mmap_reader)
    next(munmap_reader)

    mmap_dict = dict()
    for row in mmap_reader:
        if row[2] == "MAP_FAILED":
            continue
        key = (row[2], row[5])
        if key not in mmap_dict:
            mmap_dict[key] = []
        mmap_dict[key].append(datetime.strptime(str(row[1]), '%H:%M:%S.%f'))

    munmap_dict = dict()
    for row in munmap_reader:
        if row[2] == "-1":
            continue
        key = (row[4], row[5])
        if key not in munmap_dict:
            munmap_dict[key] = []
        munmap_dict[key].append(datetime.strptime(str(row[1]), '%H:%M:%S.%f'))

    plot_values = []
    for key in mmap_dict:
        if key in munmap_dict:
            mmap_list = mmap_dict[key]
            mmap_list.sort()
            munmap_list = munmap_dict[key]
            munmap_list.sort()
            mmap_size = len(mmap_list)
            munmap_size = len(munmap_list)
            maxtime = 0.0
            for index in range(mmap_size):
                if index >= munmap_size:
                    break
                delta = munmap_dict[key][index] - mmap_dict[key][index]
                time_in_seconds = delta.total_seconds()
                if time_in_seconds < 0.0:
                    time_in_seconds = -1 * time_in_seconds
                maxtime = max(maxtime, time_in_seconds)
            plot_values.append([key[0], maxtime])
    plot_values.sort()
    num_of_bins = 500
    size_window = int(len(plot_values)/num_of_bins + (len(plot_values) % num_of_bins != 0))
    bin_plot_values = []
    maxtime = 0.0
    start_range = ""
    end_range = ""
    for idx in range(len(plot_values)):
        maxtime = max(maxtime, plot_values[idx][1])
        if ((idx+1)%size_window) == 1:
           start_range = plot_values[idx][0]
        if ((idx+1)%size_window) == 0:
            end_range = plot_values[idx][0]
            bin_plot_values.append([start_range + "-" + end_range, maxtime])
            maxtime = 0.0
    if len(plot_values)%size_window != 0:
        end_range = plot_values[idx][0]
        bin_plot_values.append([start_range + "-" + end_range, maxtime])
    plot_values = bin_plot_values
    plt.rc('axes', titlesize=80)
    plt.rc('axes', labelsize=75)
    plt.rc('xtick', labelsize=15)
    plt.rc('ytick', labelsize=40)
    fig = plt.figure(figsize=(100,100), tight_layout = True)
    plt.bar([i+1 for i in range(len(plot_values))], [math.log(x[1]*1000000,10) for x in plot_values])
    plt.xticks([i+1 for i in range(len(plot_values))], [x[0] for x in plot_values], rotation = 75)
    plt.title("Lifespan-",trace_name)
    plt.xlabel("Virtual Address")
    plt.ylabel("Lifespan in log(microsecs)")
    fig.align_labels()
    plt.savefig("graphs/" + trace_name + "-lifespan", dpi = 150)


def draw_mem_memory_histograms(trace_name):
    mmap_file = open('results/mmap.csv')
    munmap_file = open('results/munmap.csv')
    brk_file = open('results/brk.csv')

    mmap_reader = csv.reader(mmap_file)
    munmap_reader = csv.reader(munmap_file)
    brk_reader = csv.reader(brk_file)
    next(mmap_reader)
    next(munmap_reader)
    next(brk_reader)

    bins = 100
    mmap_sizes = [math.log(int(i[5])) for i in mmap_reader]
    hist = [0] * bins
    interval_size = math.ceil(max(mmap_sizes) / bins)
    for i in mmap_sizes:
        hist[int(i // interval_size)] += i

    plt.bar([i for i in range(bins)], hist)

    plt.ylabel('Memory')
    plt.xlabel('Log(Memory)')
    plt.savefig('graphs/' + trace_name + '-memmem-hist')

def draw_mem_count_histograms(trace_name):
    mmap_file = open('results/mmap.csv')
    munmap_file = open('results/munmap.csv')
    brk_file = open('results/brk.csv')

    mmap_reader = csv.reader(mmap_file)
    munmap_reader = csv.reader(munmap_file)
    brk_reader = csv.reader(brk_file)
    next(mmap_reader)
    next(munmap_reader)
    next(brk_reader)

    mmap_sizes = [math.log(int(i[5])) for i in mmap_reader]
    plt.hist(mmap_sizes, bins=100, log=True)

    plt.ylabel('Count')
    plt.xlabel('Log(Memory)')
    plt.savefig('graphs/' + trace_name + '-mem-hist')

if __name__ == "__main__":
    trace_names = ["levels", "resize", "rotate", "unsharp"]
    for trace_name in trace_names:
        print("### Running " + trace_name + " ###")
        strace_file = open("strace_logs/" + trace_name + ".txt", "r")

        syscall_to_args_map = {
            "mmap": ["addr", "length", "prot", "flags", "fd", "offset"],
            "mmap_anon": ["addr", "length", "prot", "flags", "fd", "offset"],
            "munmap": ["addr", "length"],
            "mprotect": ["addr", "length", "prot"],
            "brk": ["addr"],
            "shmdt": ["shmaddr"],
            "shmat": ["shmid", "shmaddr", "shmflg"],
        }

        metadata_headers = ["pid", "timestamp", "ret_val", "duration"]
        syscall_to_args_map = {key: metadata_headers + syscall_to_args_map[key] for key in syscall_to_args_map}
        syscall_results_map = {key: [syscall_to_args_map[key]] for key in syscall_to_args_map}
        syscall_to_stacks_map = dict()

        for line in strace_file.readlines():
            for call_to_parse in syscall_to_args_map:
                if " " + call_to_parse + "(" in line:
                    if "<unfinished ...>" not in line:
                        arguments = parse_call(line, call_to_parse)
                        syscall_results_map[call_to_parse].append(arguments)
                        if call_to_parse == "mmap" and ("MAP_ANON" in arguments[7] or "MAP_ANONYMOUS" in arguments[7]):
                            syscall_results_map["mmap_anon"].append(arguments)
                    else:
                        arguments = parse_call_for_unfinished(line, call_to_parse)
                        if arguments[0] + call_to_parse not in syscall_to_stacks_map:
                            syscall_to_stacks_map[arguments[0] + call_to_parse] = []
                        syscall_to_stacks_map[arguments[0] + call_to_parse].append(arguments)
                    break
                elif "<... " + call_to_parse + " resumed>" in line:
                    fields = get_fields_for_resumed(line)
                    arguments = syscall_to_stacks_map[fields[0] + call_to_parse].pop()
                    arguments.insert(2, fields[-2])
                    arguments.insert(3, fields[-1])
                    syscall_results_map[call_to_parse].append(arguments)
                    if call_to_parse == "mmap" and ("MAP_ANON" in arguments[7] or "MAP_ANONYMOUS" in arguments[7]):
                            syscall_results_map["mmap_anon"].append(arguments)
                    break

        # Save results of each call in their own csv
        for call_name in syscall_to_args_map:
            print("Saving results/", call_name + ".csv")
            call_results_file = open("results/" + call_name + ".csv", "w")
            mmap_csv = csv.writer(call_results_file)
            mmap_csv.writerows(syscall_results_map[call_name])
            call_results_file.close()

        plt.clf()
        #draw_mem_boxplot(trace_name)
        print("Generated boxplot")
        plt.clf()
        #draw_line_chart_mem_use(trace_name)
        print("Generated mem-use")
        plt.clf()
        #draw_bar_chart_mem_lifespan_with_bin(trace_name)
        print("Generated lifespan")
        draw_mem_count_histograms(trace_name)
        print("Generated mem-histogram")
        draw_mem_memory_histograms(trace_name)
        print("Generated mem-mem-histogram")


        print("Done")
