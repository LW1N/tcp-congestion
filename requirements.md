# Project Overview (General Requirements)

## Goal: to provide students with hands-on experience in designing, implementing, testing, and evaluating computer networks.

## Each project must include:
- Network design and architecture
- Implementation using the specified or approved networking tools
- At least three meaningful experimental scenarios
- Quantitative performance evaluation
- Analysis and discussion of the results
- A comparison between alternative designs, protocols, or configurations
- Conclusions and engineering recommendations

## Regardless of topic, each team must demonstrate a clear design → implementation → experimentation → analysis process.
### Project Proposal:
- Selected project option
- Team members
- Problem statement
- Proposed network architecture
- Tools to be used
- Planned experiments
- Metrics to be collected
- Expected outcomes

### Implementation
Students must build and demonstrate a functioning network environment.
The implementation should be sufficiently complex to demonstrate graduate-level understanding of computer networking concepts.

### Experimental Evaluation
At least three meaningful experimental scenarios must be performed.
Simply demonstrating that the network operates correctly is not sufficient.
Students must modify network conditions or configurations and quantitatively evaluate the resulting behavior.

### Final Report
Submit a 6–8 page technical report containing:
1. Introduction and problem statement
2. Background
3. Network architecture/design
4. Implementation methodology
5. Experimental scenarios
6. Results
7. Analysis and discussion
8. Design recommendations
9. Conclusion
10. References
Network diagrams, tables, graphs, screenshots, and packet captures should be included where appropriate.

### Presentation and Demonstration
Each team will give a final presentation explaining:
- The problem being investigated
- Network architecture
- Implementation
- Experimental scenarios
- Major results
- Engineering conclusions
A short demonstration of the implemented network should also be provided.

## Evaluation Criteria, Projects will be evaluated based on:
- Network design and technical complexity – 20%
- Correct implementation – 20%
- Quality of experiments – 20%
- Performance analysis and interpretation – 20%
- Final report – 10%
- Presentation and demonstration – 10%
Particular emphasis will be placed on ability to explain why the network behaves as observed, rather than simply presenting configurations or screenshots.

## Important:
A project that only builds and configures a network without meaningful experimentation and analysis will not receive full credit.
The objective is to use experimental evidence to understand network behavior and make well-supported engineering recommendations.



# Project Choice: TCP Congestion and Network Performance Analysis

## Objective: Investigate how TCP behaves when multiple users compete for limited network resources.

## Tools
Mininet, iperf3, Wireshark

## Project Specific Requirements:
Create a network containing multiple hosts communicating through one or more bottleneck links.
Generate TCP and UDP traffic and study how network conditions affect application performance.

### Possible Experimental Scenarios:
1. Single TCP connection as a baseline
2. Multiple TCP connections competing for bandwidth
3. TCP and UDP traffic sharing the same bottleneck
4. Different bandwidth and propagation-delay configurations
5. Packet loss introduced into the network

### Metrics
Measure and analyze:
- Throughput
- Round-trip time
- Packet loss
- Jitter
- Bandwidth utilization
- TCP retransmissions
- Fairness between competing flows
Wireshark captures should be used to explain important TCP behavior observed during the experiments.
