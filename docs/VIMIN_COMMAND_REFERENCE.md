# VIMIN VM-S100-0800MS — CGI Command Reference

Discovered 2026-11-01 from the device's own JavaScript registry
(`js/url.js`) and live-verified against `10.41.8.33` (fw 3.5.0.10).
258 read (`get.cgi`) and 257 write (`set.cgi`) commands.

**Conventions**
- Reads: `GET cgi/get.cgi?cmd=<name>`; writes: `POST cgi/set.cgi?cmd=<name>` (form-encoded, see `switch_models/vm_s100_0800ms.py:_form_post`).
- Sub-parameter queries use extra query args: `cgi/get.cgi?cmd=diag_opticalIntf&port=0`. A `cmd` value that embeds `?...` returns 502 'CGI was not CGI/1.1 compliant'.
- `*_Edit` / `*_Add` GETs return *form scaffolding* (valid ranges/defaults), not table data.
- Firmware returns i18n templates (`lang('ns','lblKey')`) for display strings; `csp_api/normalizers.py` maps them to snake_case tokens.

**Status legend**: ✅ live (returns data) · ⬜ form-scaffold or empty (endpoint exists) · ❌ 502/not-CGI-compliant · ➖ accepted but no payload on this firmware


## Home

| GET cmd | status | SET cmds |
|---|---|---|
| `home_debug` | ✅ | `home_debugDel` |
| `home_login` | ➖ empty | `home_loginAuth` |
| `home_loginStatus` | ➖ empty | — |
| `home_main` | ✅ | — |
| `home_monitor` | ✅ | — |
| `sys_lang` | ❌ 502 | `sys_lang` |
| — | | `home_logout` |
| — | | `home_save` |

## Status

| GET cmd | status | SET cmds |
|---|---|---|
| `lag_mgmt` | ✅ | — |
| `log_syslog` | ✅ | — |
| `mac_miscStatus` | ✅ | `mac_miscStatus` |
| `panel_info` | ✅ | — |
| `panel_layout` | ✅ | — |
| `port_bwutilz` | ✅ | — |
| `port_cnt` | ✅ | `port_cntClear` |
| `port_errDisableStatus` | ✅ | `port_errDisableStatus` |
| `sys_bindUser` | ❌ 502 | — |
| `sys_cpumem` | ✅ | — |
| `sys_sysinfo` | ✅ | `sys_sysinfo` |
| `sys_sysinfoEdit` | ✅ | — |
| — | | `log_clear` |

## Network

| GET cmd | status | SET cmds |
|---|---|---|
| `sys_dns` | ✅ | `sys_dns`, `sys_dnsAdd`, `sys_dnsDel`, `sys_dnsHosts`, `sys_dnsHostsAdd`, `sys_dnsHostsDel` |
| `sys_dnsHosts` | ✅ | `sys_dnsHosts`, `sys_dnsHostsAdd`, `sys_dnsHostsDel` |
| `sys_ip` | ✅ | `sys_ip`, `sys_ipv4`, `sys_ipv6` |
| `sys_ipv4` | ❌ 502 | `sys_ipv4` |
| `sys_ipv6` | ❌ 502 | `sys_ipv6` |
| `time_time` | ✅ | `time_time` |

## Port

| GET cmd | status | SET cmds |
|---|---|---|
| `lag_lacp` | ✅ | `lag_lacp`, `lag_lacpEdit` |
| `lag_lacpEdit` | ✅ | `lag_lacpEdit` |
| `lag_mgmtEdit` | ✅ | `lag_mgmtEdit` |
| `lag_port` | ✅ | `lag_portEdit` |
| `lag_portEdit` | ✅ | `lag_portEdit` |
| `port_eee` | ✅ | `port_eeeEdit` |
| `port_eeeEdit` | ✅ | `port_eeeEdit` |
| `port_errDisable` | ✅ | `port_errDisable` |
| `port_jumbo` | ✅ | `port_jumbo` |
| `port_port` | ✅ | `port_portEdit` |
| `port_portEdit` | ✅ | `port_portEdit` |
| — | | `lag_mgmt` |

## PoE

| GET cmd | status | SET cmds |
|---|---|---|
| `poe_port` | ➖ empty | `poe_portApply`, `poe_portRestart`, `poe_portRestore` |

## VLAN

| GET cmd | status | SET cmds |
|---|---|---|
| `vlan_conf` | ✅ | `vlan_conf` |
| `vlan_create` | ✅ | `vlan_create` |
| `vlan_membership` | ✅ | `vlan_membershipEdit` |
| `vlan_membershipEdit` | ❌ 502 | `vlan_membershipEdit` |
| `vlan_port` | ✅ | `vlan_portEdit` |
| `vlan_portEdit` | ➖ empty | `vlan_portEdit` |
| — | | `vlan_del` |
| — | | `vlan_edit` |

## Mac VLAN

| GET cmd | status | SET cmds |
|---|---|---|
| `vlanmac_binding` | ✅ | `vlanmac_binding`, `vlanmac_bindingDel` |
| `vlanmac_group` | ✅ | `vlanmac_group`, `vlanmac_groupDel` |

## Voice VLAN

| GET cmd | status | SET cmds |
|---|---|---|
| `erps_config` | ✅ | `erps_config` |
| `erps_portEdit` | ✅ | `erps_portEdit` |
| `vlanvoice_oui` | ✅ | `vlanvoice_oui`, `vlanvoice_ouiDel` |
| `vlanvoice_portEdit` | ✅ | `vlanvoice_portEdit` |
| `vlanvoice_prop` | ✅ | `vlanvoice_prop` |

## Protocol VLAN

| GET cmd | status | SET cmds |
|---|---|---|
| `vlanprotocol_binding` | ✅ | `vlanprotocol_binding`, `vlanprotocol_bindingDel` |
| `vlanprotocol_group` | ✅ | `vlanprotocol_group`, `vlanprotocol_groupDel` |

## Surveillance VLAN

| GET cmd | status | SET cmds |
|---|---|---|
| `gvrp_member` | ✅ | — |
| `gvrp_portCnt` | ✅ | — |
| `gvrp_prop` | ✅ | `gvrp_prop`, `gvrp_propEdit` |
| `gvrp_propEdit` | ✅ | `gvrp_propEdit` |
| `vlansurveillance_oui` | ✅ | `vlansurveillance_oui`, `vlansurveillance_ouiDel` |
| `vlansurveillance_portEdit` | ✅ | `vlansurveillance_portEdit` |
| `vlansurveillance_prop` | ✅ | `vlansurveillance_prop` |
| — | | `gvrp_portClr` |

## Multicast

| GET cmd | status | SET cmds |
|---|---|---|
| `mcast_genFilter` | ✅ | `mcast_genFilterEdit` |
| `mcast_genFilterEdit` | ✅ | `mcast_genFilterEdit` |
| `mcast_genFwdAll` | ✅ | `mcast_genFwdAllAdd`, `mcast_genFwdAllDel`, `mcast_genFwdAllEdit` |
| `mcast_genFwdAllAdd` | ✅ | `mcast_genFwdAllAdd` |
| `mcast_genFwdAllEdit` | ❌ 502 | `mcast_genFwdAllEdit` |
| `mcast_genGroup` | ✅ | `mcast_genGroupAdd`, `mcast_genGroupDel`, `mcast_genGroupEdit` |
| `mcast_genGroupAdd` | ✅ | `mcast_genGroupAdd` |
| `mcast_genGroupEdit` | ✅ | `mcast_genGroupEdit` |
| `mcast_genProfile` | ✅ | `mcast_genProfileAdd`, `mcast_genProfileDel`, `mcast_genProfileEdit` |
| `mcast_genProfileAdd` | ✅ | `mcast_genProfileAdd` |
| `mcast_genProfileEdit` | ✅ | `mcast_genProfileEdit` |
| `mcast_genProp` | ✅ | `mcast_genProp` |
| `mcast_genRouter` | ✅ | `mcast_genRouterAdd`, `mcast_genRouterEdit` |
| `mcast_genRouterAdd` | ✅ | `mcast_genRouterAdd` |
| `mcast_genRouterEdit` | ✅ | `mcast_genRouterEdit` |
| `mcast_genThrot` | ✅ | `mcast_genThrotEdit` |
| `mcast_genThrotEdit` | ✅ | `mcast_genThrotEdit` |
| `mcast_igmpProp` | ✅ | `mcast_igmpProp`, `mcast_igmpPropEdit` |
| `mcast_igmpPropEdit` | ✅ | `mcast_igmpPropEdit` |
| `mcast_igmpQuerier` | ✅ | `mcast_igmpQuerierEdit` |
| `mcast_igmpQuerierEdit` | ✅ | `mcast_igmpQuerierEdit` |
| `mcast_igmpStat` | ✅ | `mcast_igmpStatClear` |
| `mcast_mldProp` | ✅ | `mcast_mldProp`, `mcast_mldPropEdit` |
| `mcast_mldPropEdit` | ✅ | `mcast_mldPropEdit` |
| `mcast_mldStat` | ✅ | `mcast_mldStatClear` |
| `mcast_mvrGroup` | ✅ | `mcast_mvrGroupAdd`, `mcast_mvrGroupDel`, `mcast_mvrGroupEdit` |
| `mcast_mvrGroupAdd` | ✅ | `mcast_mvrGroupAdd` |
| `mcast_mvrGroupEdit` | ✅ | `mcast_mvrGroupEdit` |
| `mcast_mvrPort` | ✅ | `mcast_mvrPortEdit` |
| `mcast_mvrPortEdit` | ✅ | `mcast_mvrPortEdit` |
| `mcast_mvrProp` | ✅ | `mcast_mvrProp` |

## MAC Address Table

| GET cmd | status | SET cmds |
|---|---|---|
| `mac_dynamic` | ✅ | `mac_dynamicAging`, `mac_dynamicToStatic` |
| `mac_filter` | ✅ | `mac_filterAdd`, `mac_filterDelete`, `mac_filterEdit` |
| `mac_static` | ✅ | `mac_staticAdd`, `mac_staticDelete`, `mac_staticEdit` |
| `psecure_mac` | ✅ | `psecure_macAdd`, `psecure_macDel`, `psecure_macEdit` |

## Spanning Tree

| GET cmd | status | SET cmds |
|---|---|---|
| `stp_global` | ✅ | `stp_global` |
| `stp_intf` | ✅ | `stp_intfEdit`, `stp_intfMigrate` |
| `stp_intfEdit` | ✅ | `stp_intfEdit` |
| `stp_msti` | ✅ | `stp_mstiEdit`, `stp_mstiIntf`, `stp_mstiIntfEdit` |
| `stp_mstiEdit` | ✅ | `stp_mstiEdit` |
| `stp_mstiIntf` | ✅ | `stp_mstiIntf`, `stp_mstiIntfEdit` |
| `stp_mstiIntfEdit` | ✅ | `stp_mstiIntfEdit` |
| `stp_statistics` | ✅ | `stp_statisticsIntfClear` |
| `stp_statisticsIntf` | ✅ | `stp_statisticsIntfClear` |

## LLDP

| GET cmd | status | SET cmds |
|---|---|---|
| `lldp_local` | ✅ | — |
| `lldp_localDetail` | ❌ 502 | — |
| `lldp_medPolicy` | ✅ | `lldp_medPolicyAdd`, `lldp_medPolicyDel`, `lldp_medPolicyEdit` |
| `lldp_medPolicyAdd` | ✅ | `lldp_medPolicyAdd` |
| `lldp_medPolicyEdit` | ✅ | `lldp_medPolicyEdit` |
| `lldp_medPort` | ✅ | `lldp_medPortEdit` |
| `lldp_medPortEdit` | ❌ 502 | `lldp_medPortEdit` |
| `lldp_neighbor` | ✅ | `lldp_neighborClear` |
| `lldp_neighborDetail` | ✅ | — |
| `lldp_overload` | ✅ | — |
| `lldp_overloadDetail` | ❌ 502 | — |
| `lldp_port` | ✅ | `lldp_portEdit`, `lldp_portStatisticsClear` |
| `lldp_portEdit` | ❌ 502 | `lldp_portEdit` |
| `lldp_prop` | ✅ | `lldp_prop` |
| `lldp_statistic` | ✅ | — |
| — | | `home_refresh` |
| — | | `lldp_globalStatisticsClear` |

## IP Configuration

| GET cmd | status | SET cmds |
|---|---|---|
| `l3_v4Arp` | ✅ | `l3_v4Arp`, `l3_v4ArpAdd`, `l3_v4ArpDel`, `l3_v4ArpEdit`, `l3_v4ArpProxy` |
| `l3_v4ArpAdd` | ✅ | `l3_v4ArpAdd` |
| `l3_v4ArpProxy` | ✅ | `l3_v4ArpProxy` |
| `l3_v4Intf` | ✅ | `l3_v4IntfAdd`, `l3_v4IntfDel`, `l3_v4IntfEdit` |
| `l3_v4IntfAdd` | ✅ | `l3_v4IntfAdd` |
| `l3_v4IntfEdit` | ✅ | `l3_v4IntfEdit` |
| `l3_v4Route` | ✅ | `l3_v4RouteAdd`, `l3_v4RouteDel`, `l3_v4RouteEdit` |
| `l3_v4RouteAdd` | ✅ | `l3_v4RouteAdd` |
| `l3_v4RouteEdit` | ✅ | `l3_v4RouteEdit` |
| `l3_v6Addr` | ✅ | `l3_v6AddrAdd`, `l3_v6AddrDel` |
| `l3_v6AddrAdd` | ✅ | `l3_v6AddrAdd` |
| `l3_v6Intf` | ✅ | `l3_v6Intf`, `l3_v6IntfAdd`, `l3_v6IntfDel`, `l3_v6IntfEdit` |
| `l3_v6IntfAdd` | ✅ | `l3_v6IntfAdd` |
| `l3_v6IntfEdit` | ✅ | `l3_v6IntfEdit` |
| `l3_v6Neigh` | ✅ | `l3_v6Neigh`, `l3_v6NeighAdd`, `l3_v6NeighDel`, `l3_v6NeighEdit` |
| `l3_v6NeighAdd` | ✅ | `l3_v6NeighAdd` |
| `l3_v6Route` | ✅ | `l3_v6RouteAdd`, `l3_v6RouteDel`, `l3_v6RouteEdit` |
| `l3_v6RouteAdd` | ✅ | `l3_v6RouteAdd` |
| `l3_v6RouteEdit` | ✅ | `l3_v6RouteEdit` |

## Security

| GET cmd | status | SET cmds |
|---|---|---|
| `aaa_login` | ✅ | `aaa_loginAdd`, `aaa_loginAuth`, `aaa_loginDel`, `aaa_loginEdit` |
| `aaa_loginAdd` | ✅ | `aaa_loginAdd` |
| `aaa_loginAuth` | ✅ | `aaa_loginAuth` |
| `aaa_loginEdit` | ✅ | `aaa_loginEdit` |
| `radius_srv` | ✅ | `radius_srv`, `radius_srvAdd`, `radius_srvDel`, `radius_srvEdit` |
| `radius_srvAdd` | ✅ | `radius_srvAdd` |
| `radius_srvEdit` | ✅ | `radius_srvEdit` |
| `tacplus_srv` | ✅ | `tacplus_srv`, `tacplus_srvAdd`, `tacplus_srvDel`, `tacplus_srvEdit` |
| `tacplus_srvAdd` | ✅ | `tacplus_srvAdd` |
| `tacplus_srvEdit` | ✅ | `tacplus_srvEdit` |

## Management VLAN

| GET cmd | status | SET cmds |
|---|---|---|
| `sys_line` | ✅ | `sys_line` |
| `vlan_mgmt` | ✅ | `vlan_mgmt` |

## Management ACL

| GET cmd | status | SET cmds |
|---|---|---|
| `aclMgmt_ace` | ✅ | `aclMgmt_ace`, `aclMgmt_aceDel`, `aclMgmt_aceEdit` |
| `aclMgmt_acl` | ✅ | `aclMgmt_acl`, `aclMgmt_aclActive`, `aclMgmt_aclDeactive`, `aclMgmt_aclDel` |
| `authmgr_macAcct` | ✅ | `authmgr_macAcctAdd`, `authmgr_macAcctDel`, `authmgr_macAcctEdit` |
| `authmgr_macAcctAdd` | ✅ | `authmgr_macAcctAdd` |
| `authmgr_macAcctEdit` | ✅ | `authmgr_macAcctEdit` |
| `authmgr_port` | ✅ | `authmgr_port`, `authmgr_portEdit` |
| `authmgr_portEdit` | ✅ | `authmgr_portEdit` |
| `authmgr_prop` | ✅ | `authmgr_prop`, `authmgr_propEdit` |
| `authmgr_propEdit` | ✅ | `authmgr_propEdit` |
| `authmgr_sess` | ✅ | `authmgr_sessClear` |
| `authmgr_webAcct` | ✅ | `authmgr_webAcctAdd`, `authmgr_webAcctDel`, `authmgr_webAcctEdit` |
| `authmgr_webAcctAdd` | ✅ | `authmgr_webAcctAdd` |
| `authmgr_webAcctEdit` | ✅ | `authmgr_webAcctEdit` |
| `port_protect` | ✅ | `port_protectEdit` |
| `port_protectEdit` | ✅ | `port_protectEdit` |
| `psecure_portEdit` | ✅ | `psecure_portEdit` |
| `psecure_prop` | ✅ | `psecure_prop` |

## Strom Control

| GET cmd | status | SET cmds |
|---|---|---|
| `storm_control` | ✅ | `storm_control`, `storm_controlEdit` |
| `storm_controlEdit` | ✅ | `storm_controlEdit` |

## DoS

| GET cmd | status | SET cmds |
|---|---|---|
| `dos_port` | ✅ | `dos_portEdit` |
| `dos_portEdit` | ✅ | `dos_portEdit` |
| `dos_prop` | ✅ | `dos_prop` |

## IPSG

| GET cmd | status | SET cmds |
|---|---|---|
| `ipsg_binding` | ✅ | `ipsg_binding`, `ipsg_bindingDel` |
| `ipsg_database` | ✅ | `ipsg_database` |
| `ipsg_portEdit` | ✅ | `ipsg_portEdit` |
| `ipsg_prop` | ✅ | `ipsg_prop` |

## DAI

| GET cmd | status | SET cmds |
|---|---|---|
| `dai_portEdit` | ✅ | `dai_portEdit` |
| `dai_prop` | ✅ | `dai_prop` |
| `dai_statistics` | ✅ | `dai_statistics` |

## DHCP Snooping

| GET cmd | status | SET cmds |
|---|---|---|
| `ds_option82CID` | ✅ | `ds_option82CID`, `ds_option82CIDDel` |
| `ds_option82PortEdit` | ✅ | `ds_option82PortEdit` |
| `ds_option82Prop` | ✅ | `ds_option82Prop` |
| `ds_portEdit` | ✅ | `ds_portEdit` |
| `ds_prop` | ✅ | `ds_prop` |
| `ds_relay` | ✅ | `ds_relay` |
| `ds_statistics` | ✅ | `ds_statistics` |

## ACL

| GET cmd | status | SET cmds |
|---|---|---|
| `acl_ace` | ❌ 502 | `acl_ace`, `acl_aceDel` |
| `acl_acl` | ✅ | `acl_acl`, `acl_aclDel` |
| `acl_binding` | ✅ | `acl_binding`, `acl_bindingDel` |

## QoS

| GET cmd | status | SET cmds |
|---|---|---|
| `qos_mapCos` | ✅ | `qos_mapCos` |
| `qos_mapDscp` | ✅ | `qos_mapDscp` |
| `qos_mapIpp` | ✅ | `qos_mapIpp` |
| `qos_portEdit` | ✅ | `qos_portEdit` |
| `qos_prop` | ✅ | `qos_prop` |
| `qos_queue` | ✅ | `qos_queue` |
| `qos_rateCtrl` | ✅ | `qos_rateCtrlEdit` |
| `qos_rateCtrlEdit` | ✅ | `qos_rateCtrlEdit` |
| `qos_rateEgrQue` | ✅ | `qos_rateEgrQueEdit` |
| `qos_rateEgrQueEdit` | ✅ | `qos_rateEgrQueEdit` |

## Diagnostics

| GET cmd | status | SET cmds |
|---|---|---|
| `diag_copper` | ✅ | `diag_copper` |
| `diag_copperResult` | ❌ 502 | — |
| `diag_mirror` | ✅ | `diag_mirrorEdit` |
| `diag_mirrorEdit` | ✅ | `diag_mirrorEdit` |
| `diag_optical` | ✅ | — |
| `diag_opticalIntf` | ✅ | — |
| `diag_ping` | ✅ | `diag_ping`, `diag_pingAbort` |
| `diag_pingResult` | ✅ | — |
| `diag_pingRunning` | ✅ | — |
| `diag_techGenStatus` | ✅ | — |
| `diag_traceroute` | ✅ | `diag_traceroute`, `diag_tracerouteAbort` |
| `diag_tracerouteResult` | ✅ | — |
| `diag_tracerouteRunning` | ✅ | — |
| `log_global` | ✅ | `log_global` |
| `log_remote` | ✅ | `log_remoteAdd`, `log_remoteDel`, `log_remoteEdit` |
| `log_remoteAdd` | ✅ | `log_remoteAdd` |
| `log_remoteEdit` | ✅ | `log_remoteEdit` |
| `udld_neighbor` | ✅ | — |
| `udld_portEdit` | ✅ | `udld_portEdit` |
| `udld_prop` | ✅ | `udld_prop` |
| — | | `diag_techGen` |
| — | | `sys_reboot` |
| — | | `sys_restore` |

## Management

| GET cmd | status | SET cmds |
|---|---|---|
| `file_bakStatus` | ✅ | — |
| `file_cfg` | ✅ | — |
| `file_dualImg` | ✅ | `file_dualImg` |
| `file_img` | ✅ | — |
| `file_saveStatus` | ✅ | — |
| `file_savecfg` | ✅ | `file_savecfg` |
| `file_upStatus` | ✅ | — |
| `rmon_alarm` | ✅ | `rmon_alarmAdd`, `rmon_alarmDel`, `rmon_alarmEdit` |
| `rmon_alarmAdd` | ✅ | `rmon_alarmAdd` |
| `rmon_alarmEdit` | ❌ 502 | `rmon_alarmEdit` |
| `rmon_event` | ✅ | `rmon_eventAdd`, `rmon_eventDel`, `rmon_eventEdit` |
| `rmon_eventAdd` | ✅ | `rmon_eventAdd` |
| `rmon_eventEdit` | ❌ 502 | `rmon_eventEdit` |
| `rmon_eventLog` | ✅ | — |
| `rmon_history` | ✅ | `rmon_historyAdd`, `rmon_historyDel`, `rmon_historyEdit` |
| `rmon_historyAdd` | ✅ | `rmon_historyAdd` |
| `rmon_historyEdit` | ❌ 502 | `rmon_historyEdit` |
| `rmon_historyLog` | ✅ | — |
| `rmon_statistics` | ✅ | `rmon_statisticsClear` |
| `rmon_statisticsIntf` | ✅ | — |
| `snmp_community` | ✅ | `snmp_communityAdd`, `snmp_communityDel`, `snmp_communityEdit` |
| `snmp_communityAdd` | ✅ | `snmp_communityAdd` |
| `snmp_communityEdit` | ✅ | `snmp_communityEdit` |
| `snmp_engineID` | ✅ | `snmp_engineID`, `snmp_engineIDAdd`, `snmp_engineIDDel`, `snmp_engineIDEdit` |
| `snmp_engineIDAdd` | ✅ | `snmp_engineIDAdd` |
| `snmp_engineIDEdit` | ✅ | `snmp_engineIDEdit` |
| `snmp_group` | ✅ | `snmp_groupAdd`, `snmp_groupDel`, `snmp_groupEdit` |
| `snmp_groupAdd` | ✅ | `snmp_groupAdd` |
| `snmp_groupEdit` | ✅ | `snmp_groupEdit` |
| `snmp_notify` | ✅ | `snmp_notifyAdd`, `snmp_notifyDel`, `snmp_notifyEdit` |
| `snmp_notifyAdd` | ✅ | `snmp_notifyAdd` |
| `snmp_notifyEdit` | ✅ | `snmp_notifyEdit` |
| `snmp_trapEvent` | ✅ | `snmp_trapEvent` |
| `snmp_user` | ✅ | `snmp_userAdd`, `snmp_userDel`, `snmp_userEdit` |
| `snmp_userAdd` | ✅ | `snmp_userAdd` |
| `snmp_userEdit` | ✅ | `snmp_userEdit` |
| `snmp_view` | ✅ | `snmp_viewAdd`, `snmp_viewDel` |
| `snmp_viewAdd` | ✅ | `snmp_viewAdd` |
| `sys_acct` | ✅ | `sys_acctAdd`, `sys_acctDel`, `sys_acctEdit` |
| `sys_acctAdd` | ✅ | `sys_acctAdd` |
| `sys_acctEdit` | ✅ | `sys_acctEdit` |
| — | | `file_backup` |
| — | | `file_upgrade` |

## Notable findings (fw 3.5.0.10)

- `poe_port` returns empty — this SKU has **no PoE**.
- `sys_lang`, `sys_bindUser` → 502 (CGI not compliant on this build).
- `diag_optical` exposes **SFP DDM**: temperature, voltage, bias, TX/RX power
  (`0.60(-2.19 dBm)` format). `diag_opticalIntf&port=N` adds transceiver ID
  (vendor, PN, SN, wavelength, compliance code).
- `diag_cable` (`diag_copper`/`diag_copperResult`) is test-trigger based
  (write to start, read for result) — not exercised read-only.
- `diag_ping` / `diag_traceroute` are run via `set.cgi`; GETs return form only.
- Route `type` codes: `0=default 1=dhcp 2=directly_connected 3=static`
  (source: device's own `ipconf_ipv4_route.html` `routeType[]`).
- VLAN membership token grammar: `5T`=tagged, `1UP`=untagged+PVID, `1F`=forbidden,
  `4095P`=placeholder (drop).
- SNMP: v1/v2c community + full v3 (users/groups/views/engineID) manageable.
- Management plane state: telnet off, **ssh on, http on**, https off, snmp on.
- **Security note**: SNMP community `public` (read-only) is active, and HTTP
  management is enabled. Both acceptable on an isolated management VLAN,
  worth revisiting if the management VLAN ever bridges.

## API integration status

Normalizers implemented in `csp_api` (all live-validated):
`info` `ports` `vlans` `mac_table` `lldp` `syslog` `l3` `stp` `optics`
`mirror` `firmware` `users` `snmp`. Everything else is reachable via
`GET /switches/{name}/raw?sections=...` once mapped in
`switch_models/vm_s100_0800ms.py::get_api_endpoints`.
