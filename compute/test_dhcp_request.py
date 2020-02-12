import argparse
import re
import time

from neutron.agent.common import async_process

verbose = False
warming = False


def print_verbose(*args, **kwargs):
    if verbose:
        print(*args, **kwargs)


def print_debug(*args, **kwargs):
    if warming:
        print(*args, **kwargs)


class DhcpClientMeasurer(async_process.AsyncProcess):
    RE_DISCOVER = re.compile(r'^DHCPDISCOVER on .*')
    RE_REQUEST = re.compile(r'^DHCPREQUEST on .*')
    RE_PACK = re.compile(r'^DHCPACK from .*')
    RE_OFFER = re.compile(r'^DHCPOFFER .*')
    RE_BOUND = re.compile(r'^bound to .*')
    class_time = time.time()

    def __init__(self, interface, namespace):
        cmd = ['dhclient', '-d', '--no-pid', interface]
        super(DhcpClientMeasurer, self).__init__(cmd, namespace=namespace)

    def start(self):
        super(DhcpClientMeasurer, self).start(block=False)
        self.wait_for_discovery()
        self.wait_for_dhcp_pack()

    def wait_for_discovery(self):
        print_debug("Waiting for DHCP request")
        for line in self.iter_stderr(block=True):
            print_debug(line)
            if self.RE_DISCOVER.match(line):
                self.start_time = time.time()
                print_verbose(self.start_time, " : ", line)
                self.next_packet = self.RE_OFFER
                break
            elif self.RE_REQUEST.match(line):
                self.start_time = time.time()
                print_verbose(self.start_time, " : ", line)
                self.next_packet = self.RE_PACK
                break

    def wait_for_dhcp_pack(self):
        print_debug("Waiting for DHCP reply")
        for line in self.iter_stderr(block=True):
            print_debug(line)
            if self.next_packet.match(line):
                self.end_time = time.time()
                print_verbose(self.end_time, " : ", line)
            elif self.RE_BOUND.match(line):
                break

    def print_stats(self):
        if hasattr(self, 'start_time') and hasattr(self, 'end_time'):
            downtime = self.end_time - self.start_time
            if verbose:
                print("It took %f seconds to obtain an address" % downtime)
            else:
                print(downtime)


def parse_args():
    global verbose
    global warming

    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--namespace', help='The namespace with port that will be used for DHCP', required=True)
    parser.add_argument('-i', '--interface', help='The interface in the namespace that will be used for DHCP', required=True)
    parser.add_argument('-v', '--verbose', help='Verbose output', action='store_true')
    parser.add_argument('-d', '--debug', help='Debug output', action='store_true')
    args = parser.parse_args()
    verbose = args.verbose
    warming = args.debug
    return args


def main():
    args = parse_args() 
    # TODO: cleanup namespace
    dhclient = DhcpClientMeasurer(args.interface, args.namespace)
    dhclient.start()
    dhclient.stop()
    dhclient.print_stats()


if __name__ == "__main__":
    main()
