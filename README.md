
# Ciscoルータ操作スクリプト：ユースケース別コマンド集

## UC-01: 接続されている全端末の IP/MAC 一覧を確認したい

- **目的**：ARPテーブルから現在接続中の端末のIP・MACアドレスを一覧表示する。
- **コマンド例**：
  ```bash
  python3 router_tool.py --print-mac-list
  ```

---

## UC-02: 特定のMACアドレスの端末通信をブロック（deny）したい

- **目的**：指定したMACアドレスに対応するIPをACLにdenyとして登録する。
- **コマンド例**：
  ```bash
  python3 router_tool.py --mode deny --mac 5023.6dca.f669
  ```

---

## UC-03: 特定MACアドレスの端末の通信を許可（permit）したい

- **目的**：指定したMACアドレスのIPをACLにpermitとして追加する。
- **コマンド例**：
  ```bash
  python3 router_tool.py --mode permit --mac 5023.6dca.f669
  ```

---

## UC-04: あるポートに接続された端末の IP/MAC を確認したい

- **目的**：指定されたポートに接続された端末（IP/MAC）を一覧表示する。
- **コマンド例**：
  ```bash
  python3 router_tool.py --show-port-devices GigabitEthernet0/3
  ```

---

## UC-05: あるポートを一時的に shutdown / no shutdown したい

- **目的**：物理ポートの有効/無効化を実行する。
- **コマンド例（無効化）**：
  ```bash
  python3 router_tool.py --port-state GigabitEthernet0/3 --action disable
  ```
- **コマンド例（有効化）**：
  ```bash
  python3 router_tool.py --port-state GigabitEthernet0/3 --action enable
  ```

---

## UC-06: ルータ/スイッチに設定されているポート一覧を取得したい

- **目的**：すべての物理インターフェースの状態を一覧表示する。
- **コマンド例**：
  ```bash
  python3 router_tool.py --list-ports
  ```

---

## UC-07: VLAN構成を一覧表示して確認したい

- **目的**：定義済みのVLANとそのステータスを表示する。
- **コマンド例**：
  ```bash
  python3 router_tool.py --list-vlans
  ```

---

## UC-08: 各インターフェースに設定された VLAN を確認したい

- **目的**：インターフェースごとに割り当てられたVLANを一覧で表示する。
- **コマンド例**：
  ```bash
  python3 router_tool.py --interface-vlan-map
  ```

---

## UC-09: VLANごとに接続されている端末（IP/MAC/PORT）を一覧で確認したい

- **目的**：各VLANに属する端末のIP、MAC、接続ポートを分類表示する。
- **コマンド例**：
  ```bash
  python3 router_tool.py --list-vlan-devices
  ```

---
