from virtual_hub import generate_hub_and_spoke_top

if __name__ == "__main__":
    for h in range(42, 52, 3):
        for n in [10, 60, 100]:
            for s in [10, 60, 100]:
                output_gnf = "h_and_s_{}_{}_{}.gnf".format(h, n, s)
                generate_hub_and_spoke_top(output_gnf, int(h), int(n), int(s), False)
