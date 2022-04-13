import glob
from mono_proof import launch_monosat
from parser import reextension

instances = glob.glob("gnfs/*.gnf")
for instance in instances:
    new_file_name = instance.rstrip(".gnf") + "UNSAT.gnf"
    with open(instance, 'r') as file:
        inputs = file.readlines()
        pre_content = ''.join(inputs[:-2])
        post_content = inputs[-1]
        declare = inputs[-2]
        if declare.startswith("maximum_flow_geq"):
            declare_token = declare.split()
            others = declare_token[:-1]
            current_value = int(declare_token[-1])
            proof_file = reextension(new_file_name, 'proof')
            support_file  =reextension(new_file_name, 'support')
            while True:
                with open(new_file_name, 'w') as new_file:
                    new_value_column = others + [str(current_value)]
                    new_file.write(pre_content + '\n' + ' '.join(new_value_column) + '\n' + post_content )
                    if launch_monosat(new_file_name, proof_file, support_file):
                        print("find UNSAT instances with flow {}".format(current_value))
                        break
                    else:
                        current_value += 2
                        print("increase flow target to {}".format(current_value))

        else:
            continue