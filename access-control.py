from netmiko import ConnectHandler
import re
import argparse
import sys
import json

# ---------- 接続情報をconfig.jsonから読み込み ----------
def load_config(filename='config.json'):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"設定ファイルの読み込みに失敗しました: {e}")
        sys.exit(1)

config = load_config()

device = {
    'device_type': 'cisco_ios',
    'host': config['host'],
    'username': config['username'],
    'password': config['password'],
}

# ---------- 引数定義 ----------
parser = argparse.ArgumentParser(description="Ciscoルータ管理ツール")
parser.add_argument('--mode', choices=['deny', 'permit'], help='ACL操作: deny または permit')
parser.add_argument('--mac', help='対象のMACアドレス (例: 5023.6dca.f669)')
parser.add_argument('--print-mac-list', action='store_true', help='ARPテーブル一覧を表示')
parser.add_argument('--list-ports', action='store_true', help='全ポートの一覧を表示')
parser.add_argument('--show-port-devices', help='指定ポートに接続されたMAC/IP一覧表示 (例: GigabitEthernet0/1)')
parser.add_argument('--port-state', help='対象ポート名 (例: GigabitEthernet0/1)')
parser.add_argument('--action', choices=['disable', 'enable'], help='ポート操作: disable or enable')
parser.add_argument('--interface-vlan-map', action='store_true', help='各インターフェースに設定されているVLANを表示')
parser.add_argument('--list-vlan-devices', action='store_true', help='VLANごとの接続端末(IP/MAC/PORT)一覧を表示')

args = parser.parse_args()

# ---------- SSH接続 ----------
net_connect = ConnectHandler(**device)

# ---------- 各種情報取得 ----------
arp_output = net_connect.send_command('show arp')
mac_table_output = net_connect.send_command('show mac-address-table')
interface_output = net_connect.send_command('show ip interface brief')

# ---------- ARPテーブル整形 ----------
arp_entries = []
for line in arp_output.splitlines():
    match = re.search(r'Internet\s+(\d+\.\d+\.\d+\.\d+)\s+\d+\s+([0-9a-f\.]+)\s+ARPA\s+(\S+)', line, re.IGNORECASE)
    if match:
        arp_entries.append({
            'ip': match.group(1),
            'mac': match.group(2).lower(),
            'interface': match.group(3)
        })

# ---------- MACテーブル整形 ----------
mac_table = []
for line in mac_table_output.splitlines():
    match = re.search(r'([0-9a-f]{4}\.[0-9a-f]{4}\.[0-9a-f]{4})\s+\S+\s+(\d+)\s+(\S+)', line, re.IGNORECASE)
    if match:
        mac_table.append({'vlan': match.group(2), 'mac': match.group(1).lower(), 'port': match.group(3)})

# ---------- ARP一覧表示 ----------
if args.print_mac_list:
    print("ARPテーブル一覧:")
    for entry in arp_entries:
        print(f"IP: {entry['ip']}, MAC: {entry['mac']}, IF: {entry['interface']}")
    net_connect.disconnect()
    sys.exit(0)

# ---------- ポート一覧表示 ----------
if args.list_ports:
    print("インターフェース一覧:")
    for line in interface_output.splitlines():
        if line.startswith('GigabitEthernet') or line.startswith('FastEthernet'):
            print(line)
    net_connect.disconnect()
    sys.exit(0)

# ---------- 指定ポートに接続されたMAC/IP表示 ----------
if args.show_port_devices:
    print(f"ポート {args.show_port_devices} に接続されたMAC/IP:")
    found = False
    for mac in mac_table:
        if mac['port'] == args.show_port_devices:
            found = True
            ip_match = next((entry['ip'] for entry in arp_entries if entry['mac'] == mac['mac']), "不明")
            print(f"MAC: {mac['mac']}  IP: {ip_match}")
    if not found:
        print("接続デバイスは見つかりませんでした。")
    net_connect.disconnect()
    sys.exit(0)

# ---------- ポートのenable/disable ----------
if args.port_state and args.action:
    cmds = [f'interface {args.port_state}']
    cmds.append('shutdown' if args.action == 'disable' else 'no shutdown')
    cmds.append('exit')
    print(f"{args.port_state} を {args.action} に設定中...")
    print(net_connect.send_config_set(cmds))
    net_connect.disconnect()
    sys.exit(0)

# ---------- MACアドレス → IP をACLへ追加 ----------
if args.mode and args.mac:
    target_ip = None
    for entry in arp_entries:
        if entry['mac'] == args.mac.lower():
            target_ip = entry['ip']
            break
    if not target_ip:
        print(f"MACアドレス {args.mac} に対応するIPが見つかりませんでした。")
        net_connect.disconnect()
        sys.exit(1)
    acl_number = '102'
    cmds = [
        f'ip access-list extended {acl_number}',
        f'{args.mode} ip host {target_ip} any',
        f'{args.mode} ip any host {target_ip}',
        'exit'
    ]
    print(f"ACL {acl_number} に {args.mode} ルールを追加します...")
    print(net_connect.send_config_set(cmds))
    net_connect.disconnect()
    sys.exit(0)

# ---------- VLAN対応表表示 ----------
if args.interface_vlan_map:
    switchport_output = net_connect.send_command('show interfaces switchport')
    print("インターフェースとVLANのマッピング:")
    current_interface = ""
    access_vlan = ""
    for line in switchport_output.splitlines():
        if line.startswith("Name:"):
            current_interface = line.split()[-1]
        if "Access Mode VLAN" in line:
            match = re.search(r'Access Mode VLAN:\s+(\d+)', line)
            if match:
                access_vlan = match.group(1)
                print(f"{current_interface} → VLAN {access_vlan}")
    net_connect.disconnect()
    sys.exit(0)

# ---------- VLANごとの端末一覧表示 ----------
if args.list_vlan_devices:
    print("VLANごとの接続端末一覧:")
    vlan_device_map = {}
    for mac in mac_table:
        vlan = mac['vlan']
        port = mac['port']
        mac_addr = mac['mac']
        ip_match = next((entry['ip'] for entry in arp_entries if entry['mac'] == mac_addr), "不明")

        if vlan not in vlan_device_map:
            vlan_device_map[vlan] = []
        vlan_device_map[vlan].append({
            'ip': ip_match,
            'mac': mac_addr,
            'port': port
        })

    for vlan_id, devices in vlan_device_map.items():
        print(f"\n[VLAN {vlan_id}]")
        for d in devices:
            print(f"IP: {d['ip']}, MAC: {d['mac']}, PORT: {d['port']}")

    net_connect.disconnect()
    sys.exit(0)

# ---------- 条件に合致しない場合 ----------
print("エラー: 正しい引数が指定されていません。--help を参照してください。")
net_connect.disconnect()
sys.exit(1)
