import 'package:flutter/material.dart';
import 'package:my_app/models/blacklist_card.dart';
import 'package:my_app/models/data_from_api.dart';
import 'package:my_app/screens/blacklist/edit_blacklist.dart';
import 'package:my_app/shared/styled_text.dart';
import 'package:my_app/models/reverse_lookup.dart';

class Blacklist extends StatefulWidget {
  const Blacklist({super.key});

  @override
  State<Blacklist> createState() => _BlacklistState();
}

class _BlacklistState extends State<Blacklist> {
  // Services
  final ApiService apiService = ApiService();

  // State variables
  List blacklist = [];
  List myBlacklist = [];
  bool loading = false;
  int maxEntriesBlocked = 500;
  int maxEntriesIgnored = 500;

  @override
  void initState() {
    super.initState();
    fetchFirewallData();
  }

  Future<void> fetchFirewallData() async {
    try {
      final blacklistData = await apiService.getBlacklist();
      final myBlacklistData = await apiService.getMyBlacklist();

      setState(() {
        blacklist = blacklistData;
        myBlacklist = myBlacklistData;
      });
    } catch (e) {
      print("Error fetching data: $e");
    }
  }

  Future<String> _resolveDns(String url) async {
    final reverseLookup = ReverseLookup(ip: url);
    return await reverseLookup.resolveIpToDomain(url);
  }

  Widget _buildShowMoreButton(VoidCallback onPressed) {
    return TextButton(
      style: TextButton.styleFrom(
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
        backgroundColor: Colors.white,
      ),
      onPressed: onPressed,
      child: const Center(child: Text('Show more')),
    );
  }

  Widget _buildBlockedIPsSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 8),
          child: myBlacklist.isEmpty
              ? const StyledHeading('The blacklist is empty')
              : const StyledHeading('Blocked IPs'),
        ),
        ...blacklist.take(maxEntriesBlocked).map((entry) {
          bool isBlocked = myBlacklist.any((myentry) =>
              myentry['blacklist_entry__capturedpacket_entry__ip'] ==
              entry['capturedpacket_entry__ip']);

          if (isBlocked) {
            return FutureBuilder<String>(
              future: _resolveDns(entry['capturedpacket_entry__ip']),
              builder: (context, snapshot) {
                return BlacklistCard(
                  entry['capturedpacket_entry__ip'] ?? 'Unknown IP',
                  snapshot.data ?? 'Resolving...',
                  'blocked',
                  fetch: fetchFirewallData,
                );
              },
            );
          }
          return Container();
        }),
      ],
    );
  }

  Widget _buildIgnoredIPsSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (!blacklist.every((entry) => myBlacklist.any((myentry) =>
            myentry['blacklist_entry__capturedpacket_entry__ip'] ==
            entry['capturedpacket_entry__ip'])))
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 8),
            child: StyledHeading('Ignored IPs'),
          ),
        ...blacklist.take(maxEntriesIgnored).map((entry) {
          bool isBlocked = myBlacklist.any((myentry) =>
              myentry['blacklist_entry__capturedpacket_entry__ip'] ==
              entry['capturedpacket_entry__ip']);

          if (!isBlocked) {
            return FutureBuilder<String>(
              future: _resolveDns(entry['capturedpacket_entry__ip']),
              builder: (context, snapshot) {
                return BlacklistCard(
                  entry['capturedpacket_entry__ip'] ?? 'Unknown IP',
                  snapshot.data ?? 'Resolving...',
                  'none',
                  fetch: fetchFirewallData,
                );
              },
            );
          }
          return Container();
        }),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const StyledTitle('My Blacklist'),
        leading: IconButton(
          onPressed: fetchFirewallData,
          icon: const Icon(Icons.sync),
        ),
        actions: [
          IconButton(
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (context) => const EditBlacklist()),
              );
            },
            icon: const Icon(Icons.edit),
          ),
        ],
      ),
      body: LayoutBuilder(
        builder: (BuildContext context, BoxConstraints constraints) {
          return Container(
            height: constraints.maxHeight,
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
              child: ConstrainedBox(
                constraints: BoxConstraints(
                  minHeight: constraints.maxHeight,
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(),
                    const SizedBox(height: 16),
                    _buildBlockedIPsSection(),
                    const SizedBox(height: 16),
                    if (_hasMoreBlockedEntries())
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          _buildShowMoreButton(() {
                            setState(() => maxEntriesBlocked += 10);
                          }),
                        ],
                      ),
                    _buildIgnoredIPsSection(),
                    if (_hasMoreIgnoredEntries())
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          _buildShowMoreButton(() {
                            setState(() => maxEntriesIgnored += 10);
                          }),
                        ],
                      ),
                    const SizedBox(height: 16),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }

  bool _hasMoreBlockedEntries() {
    return blacklist
            .where((entry) => myBlacklist.any((myentry) =>
                myentry['blacklist_entry__capturedpacket_entry__ip'] ==
                entry['capturedpacket_entry__ip']))
            .length >
        maxEntriesBlocked;
  }

  bool _hasMoreIgnoredEntries() {
    return blacklist
            .where((entry) => !myBlacklist.any((myentry) =>
                myentry['blacklist_entry__capturedpacket_entry__ip'] ==
                entry['capturedpacket_entry__ip']))
            .length >
        maxEntriesIgnored;
  }
}
