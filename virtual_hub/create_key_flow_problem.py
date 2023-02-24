from virtual_hub import tgw_instance

if __name__ == "__main__":
    for size_lb in range(5, 8):
        for size_ub in range(size_lb, size_lb+2):
            for prob in range(5, 11):
                prob = prob / 10
                file_name = "key_flow_{}_{}_{}".format(size_lb, size_ub, prob)
                print("start {}".format(file_name))
                tgw_instance(file_name, size_lb, size_ub, prob, False)
                print("done {}".format(file_name))