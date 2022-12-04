import signal
import subprocess
import os

from mono_proof import Record, run_and_prove

max_scale = 4

instance_timeout = 200000
with open("chromatic_maze.csv", 'w') as outfile:
    for width in range(2, max_scale+1):
        for height in range(2, width+1):
            min_steps_begin = width * height // 2
            for min_steps in range(min_steps_begin, (width * height) + 1):
                # first create the gnf
                instance = 'chromatic_{}_{}_{}.gnf'.format(width, height ,min_steps)
                arugment_list = ["python3", "chromatic_maze.py", str(width), str(height), str(min_steps)]
                process = subprocess.Popen(arugment_list,
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                stdout, stderr = process.communicate()

                record = Record(instance)
                # set timeout for three hours
                signal.alarm(instance_timeout)
                try:
                    res = run_and_prove(instance, record, running_opt=["-no-check-solution", "-verb=1", "-theory-order-vsids",
                                                                       "-vsids-both", "-decide-theories",
                                                                       "-no-decide-graph-rnd",
                                                                       "-lazy-maxflow-decisions", "-conflict-min-cut",
                                                                       "-adaptive-history-clear=5"], witness_reduction=True)
                    outfile.write(str(record) + '\n')
                    if res:
                        break
                    else:
                        os.remove(instance)
                except TimeoutError:
                    outfile.write("{} timeout ({} secs) \n".format(instance, instance_timeout))
                except Exception:
                    outfile.write("{} error) \n".format(instance, instance_timeout))
                    os.remove(instance)
                finally:
                    # reset alarm
                    signal.alarm(0)

