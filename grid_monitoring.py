from jumpscale.loader import j
from jumpscale.data.time import utcnow as now

from jumpscale.clients.stellar.wrapped import Server
from jumpscale.clients.stellar.balance import AccountBalances, Balance

_THREEFOLDFOUNDATION_TFTSTELLAR_SERVICES = {"TEST": "https://testnet.threefold.io", "STD": "https://tokenservices.threefold.io"}
_HORIZON_NETWORKS = {"TEST": "https://horizon-testnet.stellar.org", "STD": "https://horizon.stellar.org"}


ASSETS = ["TFT", "FreeTFT", "TFTA", "XLM"]

def _get_horizon_server(network):
    server_url = _HORIZON_NETWORKS[network]
    server = Server(horizon_url=server_url)
    return server

def _get_free_balances(network, address):
    address = address
    balances = AccountBalances(address)
    response = _get_horizon_server(network).accounts().account_id(address).call()
    for response_balance in response["balances"]:
        balances.add_balance(Balance.from_horizon_response(response_balance))
    return balances

EXPLORERS = {
    "mainnet": "https://explorer.grid.tf/api/v1",
    "testnet": "https://explorer.testnet.grid.tf/api/v1",
    "devnet": "https://explorer.devnet.grid.tf/api/v1",
}

WALLETS = {
    "mainnet": { "addr": "GB44ZXTSQCJEIVP3ROBXXA3VXJFBSATG5HPRSGRFYLYRIHJK6K27CT2F", "TFT":1000, "XLM":20},
    "testnet": {"addr":""},
    "devnet": {"addr":""},
    "tft_faucet_testnet": {"addr":"GBK7KX7KSOK2IISWPS3LWIBWJ2XTRJCST3W5MEUKKY5NGKNO5KBF6ZQI", "TFT":10},
    "polls_mainnet": {"addr":"GBL6CIPM3CJLVTDLL5CIYGCAKOK7SZ3BXU5S3QSYDH4KCU2SZUA5VIMC", "TFT":10}, 
    "trader_mainnet": {"addr":"GA4YOREDKBA5AIUGFERRL4XRXHDX3467M7YRYQVYIPOCABZBXGQMURBY", "TFT":10},
    "itenv_mainnet": {"addr": "GDYTMB2TLKGTYGY3ZTURZ7F36BVYECQXBKZBZ6X6XSFWLUXC4VGXSUIL", "TFT":10},
    "3botdeployer_mainnet": {"addr":"GD2G5KZE37CT43RLYJL6XS5JVU7JPO7EVKWLDGC36GTW5NMLVI3FSHHG", "TFT":100},
    "3botdeployer_testnet": {"addr":"GCGZ7OFC47KA45OW4EEPPJ7NKHLY2FKRKAZFAGHUE2N6WAXGCKNZ3JPW", "TFT":100},
    "marketplace_testnet": {"addr":"GCGZ7OFC47KA45OW4EEPPJ7NKHLY2FKRKAZFAGHUE2N6WAXGCKNZ3JPW", "TFT":100},
    "activation_service_mainnet": {"addr": "GCKLGWHEYT2V63HC2VDJRDWEY3G54YSHHPOA6Q3HAPQUGA5OZDWZL7KW", "XLM":50}
}

def check_threefold_services():
    info_log = []
    for network, addr in _THREEFOLDFOUNDATION_TFTSTELLAR_SERVICES.items():
        try:
            res = j.tools.http.get(addr)
            if res.status_code != 200:
                info_log.append(f"TOKEN SERVICES: {network} :: {addr} is down 💣")
            # else:
            #     info_log.append(f"TOKEN SERVICES: {network} :: {addr} is up ✅")
        except Exception as e:
            info_log.append(f"TOKEN SERVICES: {addr} is down 💣 {e}")

    return info_log

def check_explorers():
    info_log = []
    for expname, expurl in EXPLORERS.items():
        try:
            res = j.tools.http.get(expurl)
            if res.status_code != 200:
                info_log.append(f"EXPLORER {expname} {expurl} is down 💣")
            # else:
            #     info_log.append(f"EXPLORER {expname} {expurl} is up ✅")
        except Exception as e:
            print(f"EX : {e}")
            info_log.append(f"EXPLORER {expname} {expurl} is down 💣 {e}")

    return info_log

def check_wallets():
    info_log = []
    for wname, walletinfo in WALLETS.items():
        if not walletinfo:
            print(f"skipping {wname}")
            continue
        network = "STD" if "main" in wname.lower() else "TEST"
        waddress = walletinfo.get("addr", "")
        if not waddress:
            # info_log.append(f"skipping checks for {wname} {walletinfo}")
            continue
        balances = _get_free_balances(network, waddress)
        for balance in balances.balances:
            asset_code = balance.asset_code
            if asset_code.upper() in ASSETS and asset_code in walletinfo:
                notlessthanX = walletinfo[balance.asset_code]
                if int(float(balance.balance)) < notlessthanX:
                    info_log.append(f"{wname} wallet on {network} balance {balance} is less than {notlessthanX} , needs funding") 
                else:
                    print(f"{wname} wallet on {network} balance {balance} is ok, greater than {notlessthanX}") 


    return info_log

def check_gateways():
    # Todo only check against Freefarm getways
    info_log = []
    for expname, expurl in EXPLORERS.items():
        gws_endpoint = f"{expurl}/gateways"
        try:
            res = j.tools.http.get(gws_endpoint)
            json_list = res.json()

            for gw in json_list:
                gw_id = gw["id"]
                gw_node_id = gw["node_id"]
                farm_id = gw["farm_id"]
                if farm_id not in [0, 1, 71]:
                    continue #skip none freefarm gateway
                ten_mins_ago = now().timestamp - (60 * 10)
                amonth_ago = now().timestamp - (60*60*24*30)
                if gw["updated"] < ten_mins_ago and gw["updated"] > amonth_ago:
                    info_log.append(f"{expname}:: {expurl} :: gateway {gw_id} on {gw_node_id} is down 💣")
                # else:
                #     info_log.append(f"{expname}:: {expurl} :: gateway {gw_id} on {gw_node_id} is up ✅")
        except Exception as e:
            info_log.append(str(e))

    return info_log

PUBLIC_IP_FARMS = {"devnet": "lochristi_dev_lab", "testnet": "freefarm", "mainnet": "freefarm"}
DEFAULT_EXPLORER_URLS = {
    "mainnet": "https://explorer.grid.tf/api/v1",
    "testnet": "https://explorer.testnet.grid.tf/api/v1",
    "devnet": "https://explorer.devnet.grid.tf/api/v1",
}

def get_public_ip_usage(explorer_name: str = "devnet"):
    explorer = j.clients.explorer.get_by_url(DEFAULT_EXPLORER_URLS[explorer_name])
    c = 0
    if not explorer_name in ["devnet", "testnet", "mainnet"]:
        raise j.exceptions.Value(f"Explorers: devnet, testnet, mainnet are only supported, you passed {explorer_name}")
    farm = explorer.farms.get(farm_name=PUBLIC_IP_FARMS[explorer_name])
    for ip in farm.ipaddresses:
        if not ip.reservation_id:
            continue
        c += 1
        workload = explorer.workloads.get(ip.reservation_id)
        owner_tid = workload.info.customer_tid
        user = explorer.users.get(owner_tid)
        print(f"user: {user.name:30}|\ttid: {owner_tid:<5}|\twid: {workload.id}")

    return [f"{explorer_name} IPs \n busy:: {c} | free:: {len(farm.ipaddresses)-c} | total:: {len(farm.ipaddresses)}"]

def check_grid():
    
    e1 = check_explorers()
    e2 = check_wallets()
    e3 = check_gateways()
    e4 = check_threefold_services()
    e5 = get_public_ip_usage("devnet")
    e6 = get_public_ip_usage("testnet")
    return [e1, e2, e3, e4, e5, e6]

# if __name__ == "__main__":
#     get_public_ip_usage("testnet")
