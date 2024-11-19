import 'package:flutter/material.dart';
import 'package:my_app/models/data_from_api.dart';
import 'package:my_app/screens/home/info_card.dart';
import 'package:my_app/screens/home/info_card_grid.dart';
import 'package:my_app/screens/log/log.dart';
import 'package:my_app/screens/speed_log/speed_log.dart';
import 'package:my_app/shared/styled_text.dart';

class Home extends StatefulWidget {
  const Home({super.key});

  @override
  State<Home> createState() => _HomeState();
}

class _HomeState extends State<Home> {
  final ApiService apiService = ApiService();
  String status = "Loading...";
  int blockedPackets = 0;
  int speed = 0;
  int latency = 0;

  final List<String> secondSectionCards = [
    'Option 1',
    'Option 2',
    'Option 3',
    'Option 4'
  ];
  final List<String> firstSectionCards = ['Blacklist', 'Settings', 'Log', 'Support'];

  @override
  void initState() {
    super.initState();
    fetchFirewallData();
  }

  Future<void> fetchFirewallData() async {
    try {
      final statusData = await apiService.getStatus();
      final numberOfPackets = await apiService.getBlockedPackets();
      final latestSpeed = await apiService.getLatestSpeed();
      final latestLatency = await apiService.getLatestLatency();

      setState(() {
        status = statusData['status'];
        blockedPackets = numberOfPackets;
        speed = latestSpeed;
        latency = latestLatency;
      });
    } catch (e) {
      setState(() {
        status = "error";
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const StyledTitle('Home'),
        leading: IconButton(
            onPressed: fetchFirewallData, icon: const Icon(Icons.sync)),
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
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              sectionHeading('Overview'),
              InfoCardGrid(_buildInfoCards()),
              sectionHeading('Options'),
              buildCardList(firstSectionCards),
              sectionHeading('Extras'),
              buildCardList(secondSectionCards),
            ],
          ),
        ),
      ),
    );
  }

  List<Widget> _buildInfoCards() {
    return [
      _gridCard('Status', _getStatus(status), status, _getStatusColor(status),
          'status'),
      _gridCard('Blocked Packets', Icons.error, '$blockedPackets', Colors.red,
          'blocked'),
      _gridCard(
          'Speed', Icons.error, '$speed Mb/s', _getSpeedColor(40), 'speed'),
      _gridCard(
          'Latency', Icons.error, '$latency ms', _getLatencyColor(25), 'speed'),
    ];
  }

  Widget _gridCard(
      String title, IconData icon, String value, Color color, String route) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: [
        Container(height: 40, child: StyledText(title)),
        Expanded(
          child: icon != Icons.error
              ? Center(child: Icon(icon, size: 40, color: color))
              : Center(child: StyledCardText(value)),
        ),
        Container(
          height: 40,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              IconButton(
                  onPressed: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(builder: (context) => _getRoute(route)),
                    );
                  },
                  icon: const Icon(Icons.arrow_forward_ios))
            ],
          ),
        ),
      ],
    );
  }

  IconData _getStatus(String status) {
    if (status == 'running') return Icons.task_alt;
    if (status == 'error') return Icons.do_not_disturb_on;
    return Icons.error;
  }

  Color _getSpeedColor(int speed) {
    if (speed < 50) return Colors.red;
    if (speed < 100) return Colors.orange;
    return Colors.green;
  }

  Color _getLatencyColor(int latency) {
    if (latency > 100) return Colors.red;
    if (latency > 40) return Colors.orange;
    return Colors.green;
  }

  Color _getStatusColor(String status) {
    if (status == 'running') return Colors.green;
    if (status == 'error') return Colors.red;
    return Colors.orange;
  }

  Widget _getRoute(String route) {
    if (route == 'speed') return const SpeedLog();
    if (route == 'blocked') return const Log();
    if (route == 'status') return const Log();
    return const Log();
  }

  Widget sectionHeading(String title) {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: StyledHeading(title),
    );
  }

  Widget buildCardList(List<String> cards) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        children: cards.map((title) => InfoCard(title)).toList(),
      ),
    );
  }
}
