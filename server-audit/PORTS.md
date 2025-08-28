# Server Ports and Services

Raw source: /home/yancmo/apps/server-stack-monorepo-v2/server-audit/raw/20250827T193231Z

## Listening Ports (from ss)

| Port | Proto | Bind | Process | PID |
|-----:|:-----:|:-----|:--------|----:|
| 22 | tcp | * |  |  |
| 53 | tcp | 0.0.0.0 |  |  |
| 53 | tcp | [::] |  |  |
| 80 | tcp | 0.0.0.0 |  |  |
| 443 | tcp | 0.0.0.0 |  |  |
| 3000 | tcp | * |  |  |
| 5432 | tcp | 127.0.0.1 |  |  |
| 5550 | tcp | 0.0.0.0 |  |  |
| 5550 | tcp | [::] |  |  |
| 5551 | tcp | 0.0.0.0 |  |  |
| 5551 | tcp | [::] |  |  |
| 5552 | tcp | 0.0.0.0 |  |  |
| 5552 | tcp | [::] |  |  |
| 5553 | tcp | 0.0.0.0 |  |  |
| 5553 | tcp | [::] |  |  |
| 5554 | tcp | 0.0.0.0 |  |  |
| 5554 | tcp | [::] |  |  |
| 5555 | tcp | 0.0.0.0 |  |  |
| 5555 | tcp | [::] |  |  |
| 5557 | tcp | 0.0.0.0 |  |  |
| 5557 | tcp | [::] |  |  |
| 8080 | tcp | 0.0.0.0 |  |  |
| 8080 | tcp | [::] |  |  |
| 8384 | tcp | * | syncthing | 41851 |
| 8443 | tcp | 0.0.0.0 |  |  |
| 8443 | tcp | [::] |  |  |
| 8888 | tcp | 0.0.0.0 |  |  |
| 9090 | tcp | * |  |  |
| 22000 | tcp | * | syncthing | 41851 |
| 36749 | tcp | 127.0.0.1 | code-insiders-c | 1729535 |
| 53077 | tcp | 100.98.189.105 |  |  |
| 60310 | tcp | [fd7a:115c:a1e0::bd01:bd6a] |  |  |
| 53 | udp | 0.0.0.0 |  |  |
| 53 | udp | [::] |  |  |
| 68 | udp | 192.168.50.97%enx00e04c030111 |  |  |
| 123 | udp | 0.0.0.0 |  |  |
| 123 | udp | [::] |  |  |
| 546 | udp | [fe80::529:88e6:6808:c420]%wlp3s0 |  |  |
| 546 | udp | [fe80::2e0:4cff:fe03:111]%enx00e04c030111 |  |  |
| 21027 | udp | 0.0.0.0 | syncthing | 41851 |
| 21027 | udp | [::] | syncthing | 41851 |
| 22000 | udp | * | syncthing | 41851 |
| 41641 | udp | 0.0.0.0 |  |  |
| 41641 | udp | [::] |  |  |
| 53543 | udp | 0.0.0.0 | syncthing | 41851 |
| 58636 | udp | [::] | syncthing | 41851 |

## Firewall Summary

### UFW (status excerpt)

```
Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), deny (routed)
New profiles: skip

To                         Action      From
--                         ------      ----
22/tcp (OpenSSH)           ALLOW IN    Anywhere                  
Anywhere on tailscale0     ALLOW IN    Anywhere                  
80/tcp                     ALLOW IN    Anywhere                  
443/tcp                    ALLOW IN    Anywhere                  
8080 on tailscale0         ALLOW IN    Anywhere                  
8443 on tailscale0         ALLOW IN    Anywhere                  
22000 on tailscale0        ALLOW IN    Anywhere                  
8384 on tailscale0         ALLOW IN    Anywhere                  
9090                       ALLOW IN    Anywhere                  
8888/tcp                   ALLOW IN    Anywhere                  
22/tcp                     ALLOW IN    4.245.0.0/17               # GitHub Actions Runner
22/tcp                     ALLOW IN    4.245.128.0/17             # GitHub Actions Runner
22/tcp                     ALLOW IN    4.246.0.0/17               # GitHub Actions Runner
22/tcp                     ALLOW IN    4.246.128.0/17             # GitHub Actions Runner
22/tcp                     ALLOW IN    4.249.0.0/17               # GitHub Actions Runner
22/tcp                     ALLOW IN    4.249.128.0/17             # GitHub Actions Runner
22/tcp                     ALLOW IN    4.255.0.0/17               # GitHub Actions Runner
22/tcp                     ALLOW IN    9.163.0.0/16               # GitHub Actions Runner
22/tcp                     ALLOW IN    9.169.0.0/17               # GitHub Actions Runner
22/tcp                     ALLOW IN    9.169.128.0/17             # GitHub Actions Runner
22/tcp                     ALLOW IN    9.234.0.0/17               # GitHub Actions Runner
22/tcp                     ALLOW IN    9.234.128.0/17             # GitHub Actions Runner
22/tcp                     ALLOW IN    13.64.0.0/16               # GitHub Actions Runner
22/tcp                     ALLOW IN    13.65.0.0/16               # GitHub Actions Runner
22/tcp                     ALLOW IN    13.66.0.0/17               # GitHub Actions Runner
22/tcp                     ALLOW IN    13.66.128.0/17             # GitHub Actions Runner
22/tcp                     ALLOW IN    13.67.128.0/20             # GitHub Actions Runner
22/tcp                     ALLOW IN    13.67.144.0/21             # GitHub Actions Runner
22/tcp                     ALLOW IN    13.67.152.0/24             # GitHub Actions Runner
22/tcp                     ALLOW IN    13.67.153.0/28             # GitHub Actions Runner
22/tcp                     ALLOW IN    13.67.153.32/27            # GitHub Actions Runner
22/tcp                     ALLOW IN    13.104.129.64/26           # GitHub Actions Runner
22/tcp                     ALLOW IN    13.104.144.64/27           # GitHub Actions Runner
22/tcp                     ALLOW IN    13.104.144.128/27          # GitHub Actions Runner
22/tcp                     ALLOW IN    13.104.144.192/27          # GitHub Actions Runner
22/tcp                     ALLOW IN    13.104.145.0/26            # GitHub Actions Runner
22/tcp                     ALLOW IN    13.104.145.192/26          # GitHub Actions Runner
22/tcp                     ALLOW IN    13.104.146.0/26            # GitHub Actions Runner
22/tcp                     ALLOW IN    13.104.146.128/25          # GitHub Actions Runner
22/tcp                     ALLOW IN    13.104.147.0/25            # GitHub Actions Runner
22/tcp                     ALLOW IN    13.104.147.128/25          # GitHub Actions Runner
22/tcp                     ALLOW IN    13.104.148.0/25            # GitHub Actions Runner
22/tcp                     ALLOW IN    13.104.149.128/25          # GitHub Actions Runner
22/tcp                     ALLOW IN    13.104.150.0/25            # GitHub Actions Runner
22/tcp                     ALLOW IN    13.104.152.128/25          # GitHub Actions Runner
22/tcp                     ALLOW IN    13.104.158.16/28           # GitHub Actions Runner
22/tcp                     ALLOW IN    13.104.158.64/26           # GitHub Actions Runner
22/tcp                     ALLOW IN    13.104.158.176/28          # GitHub Actions Runner
22/tcp                     ALLOW IN    13.104.192.0/21            # GitHub Actions Runner
22/tcp                     ALLOW IN    13.104.208.64/27           # GitHub Actions Runner
22/tcp                     ALLOW IN    13.104.208.96/27           # GitHub Actions Runner
22/tcp                     ALLOW IN    13.104.208.128/27          # GitHub Actions Runner
22/tcp                     ALLOW IN    13.104.208.160/28          # GitHub Actions Runner
22/tcp                     ALLOW IN    13.104.208.192/26          # GitHub Actions Runner
22/tcp                     ALLOW IN    13.104.209.0/24            # GitHub Actions Runner
22/tcp                     ALLOW IN    13.104.210.0/24            # GitHub Actions Runner
22/tcp                     ALLOW IN    13.104.211.0/25            # GitHub Actions Runner
22/tcp                     ALLOW IN    13.104.213.0/25            # GitHub Actions Runner
22/tcp                     ALLOW IN    13.104.214.0/25            # GitHub Actions Runner
22/tcp                     ALLOW IN    13.104.214.128/25          # GitHub Actions Runner
22/tcp                     ALLOW IN    13.104.215.0/25            # GitHub Actions Runner
22/tcp                     ALLOW IN    13.104.217.0/25            # GitHub Actions Runner
22/tcp                     ALLOW IN    13.104.218.128/25          # GitHub Actions Runner
22/tcp                     ALLOW IN    13.104.219.128/25          # GitHub Actions Runner
22/tcp                     ALLOW IN    13.104.220.0/25            # GitHub Actions Runner
22/tcp                     ALLOW IN    13.104.220.128/25          # GitHub Actions Runner
22/tcp                     ALLOW IN    13.104.222.0/24            # GitHub Actions Runner
22/tcp                     ALLOW IN    13.104.223.0/25            # GitHub Actions Runner
22/tcp                     ALLOW IN    13.105.14.0/25             # GitHub Actions Runner
22/tcp                     ALLOW IN    13.105.14.128/26           # GitHub Actions Runner
22/tcp                     ALLOW IN    13.105.17.0/26             # GitHub Actions Runner
22/tcp                     ALLOW IN    13.105.17.64/26            # GitHub Actions Runner
22/tcp                     ALLOW IN    13.105.17.128/26           # GitHub Actions Runner
```
### Packet Filter (iptables/nft excerpt)

```
-P INPUT DROP
-P FORWARD DROP
-P OUTPUT ACCEPT
-N DOCKER
-N DOCKER-BRIDGE
-N DOCKER-CT
-N DOCKER-FORWARD
-N DOCKER-ISOLATION-STAGE-1
-N DOCKER-ISOLATION-STAGE-2
-N DOCKER-USER
-N ts-forward
-N ts-input
-N ufw-after-forward
-N ufw-after-input
-N ufw-after-logging-forward
-N ufw-after-logging-input
-N ufw-after-logging-output
-N ufw-after-output
-N ufw-before-forward
-N ufw-before-input
-N ufw-before-logging-forward
-N ufw-before-logging-input
-N ufw-before-logging-output
-N ufw-before-output
-N ufw-logging-allow
-N ufw-logging-deny
-N ufw-not-local
-N ufw-reject-forward
-N ufw-reject-input
-N ufw-reject-output
-N ufw-skip-to-policy-forward
-N ufw-skip-to-policy-input
-N ufw-skip-to-policy-output
-N ufw-track-forward
-N ufw-track-input
-N ufw-track-output
-N ufw-user-forward
-N ufw-user-input
-N ufw-user-limit
-N ufw-user-limit-accept
-N ufw-user-logging-forward
-N ufw-user-logging-input
-N ufw-user-logging-output
-N ufw-user-output
-A INPUT -j ts-input
-A INPUT -j ufw-before-logging-input
-A INPUT -j ufw-before-input
-A INPUT -j ufw-after-input
-A INPUT -j ufw-after-logging-input
-A INPUT -j ufw-reject-input
-A INPUT -j ufw-track-input
-A FORWARD -j ts-forward
-A FORWARD -j DOCKER-USER
-A FORWARD -j DOCKER-FORWARD
-A FORWARD -j ufw-before-logging-forward
-A FORWARD -j ufw-before-forward
-A FORWARD -j ufw-after-forward
-A FORWARD -j ufw-after-logging-forward
-A FORWARD -j ufw-reject-forward
-A FORWARD -j ufw-track-forward
-A OUTPUT -j ufw-before-logging-output
-A OUTPUT -j ufw-before-output
-A OUTPUT -j ufw-after-output
-A OUTPUT -j ufw-after-logging-output
-A OUTPUT -j ufw-reject-output
-A OUTPUT -j ufw-track-output
-A DOCKER -d 172.18.0.11/32 ! -i br-bea0b6e2e3a9 -o br-bea0b6e2e3a9 -p tcp -m tcp --dport 5553 -j ACCEPT
-A DOCKER -d 172.18.0.10/32 ! -i br-bea0b6e2e3a9 -o br-bea0b6e2e3a9 -p tcp -m tcp --dport 5555 -j ACCEPT
-A DOCKER -d 172.18.0.9/32 ! -i br-bea0b6e2e3a9 -o br-bea0b6e2e3a9 -p tcp -m tcp --dport 5550 -j ACCEPT
-A DOCKER -d 172.18.0.7/32 ! -i br-bea0b6e2e3a9 -o br-bea0b6e2e3a9 -p tcp -m tcp --dport 5552 -j ACCEPT
-A DOCKER -d 172.18.0.6/32 ! -i br-bea0b6e2e3a9 -o br-bea0b6e2e3a9 -p tcp -m tcp --dport 5557 -j ACCEPT
-A DOCKER -d 172.18.0.3/32 ! -i br-bea0b6e2e3a9 -o br-bea0b6e2e3a9 -p tcp -m tcp --dport 5551 -j ACCEPT
-A DOCKER -d 172.18.0.2/32 ! -i br-bea0b6e2e3a9 -o br-bea0b6e2e3a9 -p tcp -m tcp --dport 5554 -j ACCEPT
-A DOCKER ! -i br-bea0b6e2e3a9 -o br-bea0b6e2e3a9 -j DROP
-A DOCKER ! -i docker0 -o docker0 -j DROP
-A DOCKER-BRIDGE -o br-bea0b6e2e3a9 -j DOCKER
-A DOCKER-BRIDGE -o docker0 -j DOCKER
-A DOCKER-CT -o br-bea0b6e2e3a9 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A DOCKER-CT -o docker0 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A DOCKER-FORWARD -j DOCKER-CT
-A DOCKER-FORWARD -j DOCKER-ISOLATION-STAGE-1
-A DOCKER-FORWARD -j DOCKER-BRIDGE
-A DOCKER-FORWARD -i br-bea0b6e2e3a9 -j ACCEPT
-A DOCKER-FORWARD -i docker0 -j ACCEPT
-A DOCKER-ISOLATION-STAGE-1 -i br-bea0b6e2e3a9 ! -o br-bea0b6e2e3a9 -j DOCKER-ISOLATION-STAGE-2
-A DOCKER-ISOLATION-STAGE-1 -i docker0 ! -o docker0 -j DOCKER-ISOLATION-STAGE-2
-A DOCKER-ISOLATION-STAGE-2 -o docker0 -j DROP
-A DOCKER-ISOLATION-STAGE-2 -o br-bea0b6e2e3a9 -j DROP
-A ts-forward -i tailscale0 -j MARK --set-xmark 0x40000/0xff0000
-A ts-forward -m mark --mark 0x40000/0xff0000 -j ACCEPT
-A ts-forward -s 100.64.0.0/10 -o tailscale0 -j DROP
-A ts-forward -o tailscale0 -j ACCEPT
-A ts-input -s 100.98.189.105/32 -i lo -j ACCEPT
-A ts-input -s 100.115.92.0/23 ! -i tailscale0 -j RETURN
-A ts-input -s 100.64.0.0/10 ! -i tailscale0 -j DROP
-A ts-input -i tailscale0 -j ACCEPT
-A ts-input -p udp -m udp --dport 41641 -j ACCEPT
-A ufw-after-input -p udp -m udp --dport 137 -j ufw-skip-to-policy-input
-A ufw-after-input -p udp -m udp --dport 138 -j ufw-skip-to-policy-input
-A ufw-after-input -p tcp -m tcp --dport 139 -j ufw-skip-to-policy-input
-A ufw-after-input -p tcp -m tcp --dport 445 -j ufw-skip-to-policy-input
-A ufw-after-input -p udp -m udp --dport 67 -j ufw-skip-to-policy-input
-A ufw-after-input -p udp -m udp --dport 68 -j ufw-skip-to-policy-input
-A ufw-after-input -m addrtype --dst-type BROADCAST -j ufw-skip-to-policy-input
-A ufw-after-logging-forward -m limit --limit 3/min --limit-burst 10 -j LOG --log-prefix "[UFW BLOCK] "
-A ufw-after-logging-input -m limit --limit 3/min --limit-burst 10 -j LOG --log-prefix "[UFW BLOCK] "
-A ufw-before-forward -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A ufw-before-forward -p icmp -m icmp --icmp-type 3 -j ACCEPT
-A ufw-before-forward -p icmp -m icmp --icmp-type 11 -j ACCEPT
-A ufw-before-forward -p icmp -m icmp --icmp-type 12 -j ACCEPT
-A ufw-before-forward -p icmp -m icmp --icmp-type 8 -j ACCEPT
-A ufw-before-forward -j ufw-user-forward
-A ufw-before-input -i lo -j ACCEPT
-A ufw-before-input -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A ufw-before-input -m conntrack --ctstate INVALID -j ufw-logging-deny
-A ufw-before-input -m conntrack --ctstate INVALID -j DROP
-A ufw-before-input -p icmp -m icmp --icmp-type 3 -j ACCEPT
-A ufw-before-input -p icmp -m icmp --icmp-type 11 -j ACCEPT
-A ufw-before-input -p icmp -m icmp --icmp-type 12 -j ACCEPT
-A ufw-before-input -p icmp -m icmp --icmp-type 8 -j ACCEPT
```

## Nginx Config Dump (excerpt)

```
2025/08/27 19:32:33 [warn] 1753973#1753973: the "user" directive makes sense only if the master process runs with super-user privileges, ignored in /etc/nginx/nginx.conf:1
2025/08/27 19:32:33 [warn] 1753973#1753973: duplicate MIME type "text/html" in /etc/nginx/sites-enabled/<redacted.domain>:119
2025/08/27 19:32:33 [warn] 1753973#1753973: duplicate MIME type "text/html" in /etc/nginx/sites-enabled/<redacted.domain>:173
2025/08/27 19:32:33 [warn] 1753973#1753973: duplicate MIME type "text/html" in /etc/nginx/sites-enabled/<redacted.domain>.conf:155
2025/08/27 19:32:33 [info] 1753973#1753973: Using 116KiB of shared memory for nchan in /etc/nginx/nginx.conf:61
2025/08/27 19:32:33 [info] 1753973#1753973: Using 131072KiB of shared memory for nchan in /etc/nginx/nginx.conf:61
2025/08/27 19:32:33 [warn] 1753973#1753973: conflicting server name "<redacted.domain>" on 0.0.0.0:80, ignored
2025/08/27 19:32:33 [warn] 1753973#1753973: conflicting server name "<redacted.domain>" on 0.0.0.0:80, ignored
2025/08/27 19:32:33 [warn] 1753973#1753973: conflicting server name "<redacted.domain>" on 0.0.0.0:443, ignored
2025/08/27 19:32:33 [warn] 1753973#1753973: conflicting server name "<redacted.domain>" on 0.0.0.0:443, ignored
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
2025/08/27 19:32:33 [emerg] 1753973#1753973: open() "/run/nginx.pid" failed (13: Permission denied)
nginx: configuration file /etc/nginx/nginx.conf test failed
```

## Caddyfile (excerpt)

```
cat: /etc/caddy/Caddyfile: No such file or directory
```