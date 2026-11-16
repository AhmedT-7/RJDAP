RJDAP - Reliable Job Dispatch & Aggregation Protocol
Team 17 - CSE361 Project 2 - Phase 1 (Prototype)

REQUIREMENTS:
Python 3.10 or later
Windows or Linux
No additional Python packages required

RUN BASELINE TEST:
1. Open a terminal in the RJDAP root folder.
2. Run: python -m tests.run_baseline
3. Expected output: PASS: 4 workers, 1000 tasks, 0 duplicates
4. Packet logs with timestamps are written to logs/ (server.log, worker_1..4.log).

RUN UNIT TESTS:
python -m unittest tests.test_protocol

MANUAL EXECUTION:
Terminal 1: python -m src.server
Terminal 2: python -m src.client 1
Terminal 3: python -m src.client 2
Terminal 4: python -m src.client 3
Terminal 5: python -m src.client 4

PACKET CAPTURE:
logs/baseline.pcap contains the full baseline run (open in Wireshark).
To capture again on Linux:
  sudo tcpdump -i lo -U -w logs/baseline.pcap udp port 5000
  (run the baseline test in another terminal, then stop tcpdump with Ctrl+C)
On Windows: Wireshark with Npcap, interface "Adapter for loopback traffic capture",
display filter: udp.port == 5000

PROTOCOL:
UDP, server port 5000
18-byte binary header (struct format !2sBBIHHHI), CRC32 payload checksum
Messages: WORKER_JOIN, HEARTBEAT, TASK_DISPATCH, TASK_RESULT, ACK_RESULT, STOP
Invalid packets (bad magic, length, or checksum) are logged and dropped.
Workers send a HEARTBEAT every 1 second.

TASK:
Hash search. Each task is a range of 20,000 numbers and a SHA-256 target hash
(payload "start:end:target_hex", 80 bytes). The worker finds the number in the
range whose hash matches and returns it. The server verifies the answer.
Tasks are generated from a fixed seed (17), so every run is reproducible.

LIMITATIONS:
Phase 1 baseline implementation.
Loss recovery, worker-crash recovery, and timeout-based reassignment
are Phase 2 features.

DEMO VIDEO:
https://drive.google.com/drive/folders/1ntpQXbIprXlVlUqCubvFtWgzCSf06Huw?usp=sharing
