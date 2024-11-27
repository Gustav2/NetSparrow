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
  final ApiService _apiService = ApiService();
  String _status = "Loading...";
  int _blockedIps = 0;
  int _percentageBlocked = 0;
  int _centralServerIps = 0;

  static const List<String> _secondSectionCards = [
    'Option 1',
    'Option 2',
    'Option 3',
    'Option 4'
  ];
  static const List<String> _firstSectionCards = ['Blacklist', 'Settings', 'Log', 'Support'];

  @override
  void initState() {
    super.initState();
    _fetchFirewallData();
  }

  Future<void> _fetchFirewallData() async {
    setState(() {
      _status = "Loading...";
    });

    try {
      final statusData = await _apiService.getStatus();
      final blockedData = await _apiService.getMyBlacklist();
      final centralServerIpsData = await _apiService.getBlacklist();

      if (!mounted) return;

      setState(() {
        _status = statusData ? 'running' : 'error';
        _blockedIps = blockedData.length;
        _centralServerIps = centralServerIpsData.length;
        _percentageBlocked = ((_blockedIps / _centralServerIps) * 100).toInt();
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _status = "error";
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const StyledTitle('Home'),
        leading: IconButton(
            onPressed: _fetchFirewallData, icon: const Icon(Icons.sync)),
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
              _sectionHeading('Overview'),
              InfoCardGrid(_buildInfoCards()),
              _sectionHeading('Options'),
              _buildCardList(_firstSectionCards),
              _sectionHeading('Extras'),
              _buildCardList(_secondSectionCards),
            ],
          ),
        ),
      ),
    );
  }

  List<Widget> _buildInfoCards() {
    return [
      _gridCard('Status', _getStatus(_status), _status, _getStatusColor(_status),
          'status'),
      _gridCard('Blocked Ips', Icons.error, '$_blockedIps', Colors.red,
          'blocked'),
      _gridCard(
          'Percent blocked', Icons.error, '$_percentageBlocked %', _getSpeedColor(_percentageBlocked), 'speed'),
      _gridCard(
          'Central server', Icons.error, '$_centralServerIps', _getLatencyColor(_centralServerIps), 'speed'),
    ];
  }

  Widget _gridCard(
      String title, IconData icon, String value, Color color, String route) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: [
        SizedBox(height: 40, child: StyledText(title)),
        Expanded(
          child: icon != Icons.error
              ? Icon(icon, size: 40, color: color)
              : StyledCardText(value),
        ),
        SizedBox(
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
    switch (status) {
      case 'running':
        return Icons.task_alt;
      case 'error':
        return Icons.do_not_disturb_on;
      default:
        return Icons.error;
    }
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
    switch (status) {
      case 'running':
        return Colors.green;
      case 'error':
        return Colors.red;
      default:
        return Colors.orange;
    }
  }

  Widget _getRoute(String route) {
    switch (route) {
      case 'speed':
        return const SpeedLog();
      case 'blocked':
      case 'status':
      default:
        return const Log();
    }
  }

  Widget _sectionHeading(String title) {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: StyledHeading(title),
    );
  }

  Widget _buildCardList(List<String> cards) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        children: cards.map((title) => InfoCard(title)).toList(),
      ),
    );
  }
}
