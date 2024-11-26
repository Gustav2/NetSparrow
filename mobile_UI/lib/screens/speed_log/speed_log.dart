import 'package:flutter/material.dart';
import 'package:my_app/models/data_from_api.dart';

import 'package:my_app/models/log_card.dart';
import 'package:my_app/shared/styled_text.dart';


class SpeedLog extends StatefulWidget {
  const SpeedLog({super.key});

  @override
  State<SpeedLog> createState() => _HomeState();
}

class _HomeState extends State<SpeedLog> {
  final ApiService apiService = ApiService();
  int speed = 0;
  int latency = 0;
  List log = [];
  String error = '';

  @override
  void initState() {
    super.initState();
    fetchFirewallData();
  }

  Future<void> fetchFirewallData() async {
    try {
      final latestSpeed = await apiService.getLatestSpeed();
      final latestLatency = await apiService.getLatestLatency();
      final logData = await apiService.getLogList();

      setState(() {

        speed = latestSpeed;
        latency = latestLatency;
        log = logData;
      });
    } catch (e) {
      setState(() {
        error = "Error: ${e.toString()}";
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const StyledTitle('Log'),
        leading: IconButton(onPressed: fetchFirewallData, icon: const Icon(Icons.sync)),
        actions: [
          IconButton(
            onPressed: () {},
            icon: const Icon(Icons.menu),
          ),
        ],
      ),
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [
              Color.fromARGB(255, 250, 250, 250),
              Color.fromARGB(255, 250, 250, 250),
              Color.fromARGB(255, 240, 240, 240),
              Color.fromARGB(255, 225, 225, 225),
              Color.fromARGB(255, 210, 210, 210),
            ],
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
          ),
        ),
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              tableHeading(['Timestamp', 'Speed', 'Latency']),
                for (var entry in log)
                  LogCard(entry['timestamp'], entry['speed'], entry['latency']),
            ],
          ),
        ),
      ),
    );
  }

  Widget tableHeading(List titles) {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          for (var title in titles) StyledHeading(title),
        ],
      ),
    );
  }
}