import registry


def do_query(reg:registry.Registry, args):
    relevant = {
        "ip": args.ip,
        "host": args.host,
        "dump": args.dump,
        "hosts": args.hosts,
        "latest": args.latest,
    }
    assert len([x for x in relevant.values() if x not in [None,False]]) == 1, f"Specify one of {', '.join(relevant.keys())}"

    print(f"Reading from {reg.filepath()}")

    if relevant["ip"] is not None:
        res = reg.names_of(relevant["ip"])
        print("\n".join(res))
    if relevant["host"] is not None:
        res = reg.ips_of(relevant["host"])
        print("\n".join(res))
    if relevant["dump"]:
        entries = reg.entry_lines()
        print("\n".join( entries ))
    if relevant["latest"]:
        pairs = reg.latest_pairs()
        print("\n".join( pairs ))
    if relevant["hosts"]:
        ips = reg.get_hosts()
        for ip, hostlist in ips.items():
            print(f"{ip}  {' '.join([x if x else 'NONE.INVALID' for x in hostlist])}")
