import optparse
from collections import defaultdict
from pprint import pprint as pp
import numpy as np

def parse_arguments():
    """ Specify and parse options for slingshot. """
    parser = optparse.OptionParser()

    parser.add_option('-b', '--ballista', dest='ballista',
    default='os_results.txt')
    parser.add_option('-s', '--slingshot', dest='slingshot',
    default='s_results.txt')
    (opts, _) = parser.parse_args()
    return opts

def get_results(file_descriptor):
    results = defaultdict(float)
    for line in file_descriptor:
        splitted_line = line.split()
        function = splitted_line[0]
        failure_rate = float(splitted_line[1])
        results[function] = failure_rate

    return results


def main():
    """ Main function. Is executed when the script is run. """
    opts = parse_arguments()
    with open(opts.ballista, 'r') as ballista_file:
        ballista_results = get_results(ballista_file)

    with open(opts.slingshot, 'r') as slingshot_file:
        slingshot_results = get_results(slingshot_file)

    counter = 0
    epsilon = 25.0
    not_tested_in_ballista = []
    fun_slingshot_higher = []
    fun_ballista_higher = []
    higher_rate_slingshot = 0
    higher_rate_ballista = 0
    with open('table.tex', 'w') as f:
        for fun, fail_rate in slingshot_results.iteritems():
            if ballista_results.has_key(fun):
                #difference = float(ballista_results[fun]) - float(fail_rate)
                difference =float(fail_rate) - float(ballista_results[fun])
                if abs(difference) > epsilon:
                    counter += 1
                    #print("Got difference of {}".format(difference))
                    print("Function {} : Ballista: {} Slingshot: {}".format(
                        fun, ballista_results[fun], slingshot_results[fun]))
                    f.write("{} & {} & {} & {} \\\\ \\hline\n".format(fun,
                        difference, slingshot_results[fun], ballista_results[fun]))
                    if float(fail_rate) >= float(ballista_results[fun]):
                        fun_slingshot_higher.append(fun)
                    else:
                        fun_ballista_higher.append(fun)
                if ballista_results[fun] <= slingshot_results[fun]:
                    higher_rate_slingshot += 1
                else:
                    higher_rate_ballista += 1

            else:
                not_tested_in_ballista.append(fun)
    print("Number of functions with an difference in failure rates"
            " over {}%: {}".format(epsilon, counter))
    print("{} functions were not tested by ballista"
            " : {}".format(len(not_tested_in_ballista), not_tested_in_ballista))
    print("{} of slingshot hat an higher failure rate {} of ballista".format(
        len(fun_slingshot_higher), len(fun_ballista_higher)))

    print("Ballistas average failure rate {} and std {}".format(
        np.average(ballista_results.values()),
        np.std(ballista_results.values()),))
    print("slingshot average failure rate {} and std {}".format(
        np.average(slingshot_results.values()),
        np.std(slingshot_results.values()),))

    print("failure rate increased in {} ".format(higher_rate_slingshot))
    print("failure rate decreased in {} ".format(higher_rate_ballista))


if __name__ == '__main__':
    main()
