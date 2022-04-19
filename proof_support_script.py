from mono_proof import run_and_prove, load_record, Record, reset
import glob
overwrite = False
import csv
output_file = "result.csv"
benchmark = "mx_benchmark"




Records = {}

if __name__ == "__main__":
    if not overwrite:
        with open(output_file, 'r') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
            for row in spamreader:
                record = load_record(row)
                Records[record.name]= record
    instances = glob.glob("{}/*.gnf".format(benchmark))

    with open(output_file, 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='|')
        header = Record("header")
        csvfile.write(header.print_header())
        for inst in instances:
            record = Record(inst)
            if not overwrite and inst in Records:
                if Records[inst].verification_result != "error":
                    continue
                else:
                    writer.writerow(Records[inst].get_attributes())
            else:
                try:
                    run_and_prove(inst, record)
                except:
                    print("{} unverified".format(inst))
                    record.set_verification_result("error")
                finally:
                    reset()
                writer.writerow(record.get_attributes())
                csvfile.flush()





