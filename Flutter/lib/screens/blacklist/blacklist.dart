import 'package:flutter/material.dart';
import 'package:my_app/models/blacklist_card.dart';
import 'package:my_app/models/data_from_api.dart';
import 'package:my_app/screens/blacklist/edit_blacklist.dart';
import 'package:my_app/shared/styled_text.dart';

class Blacklist extends StatefulWidget {
  const Blacklist({super.key});

  @override
  State<Blacklist> createState() => _HomeState();
}

class _HomeState extends State<Blacklist> {
  final ApiService apiService = ApiService();
  List blacklist = [];
  List myBlacklist = [];
  String ifblocked = 'none';

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

    print("Blacklist: $blacklist");

    } catch (e) {
      setState(() {
        print("Error: ${e.toString()}");
      });
      print("Error fetching data: $e");
    }
  }


  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const StyledTitle('My Blacklist'),
        leading: IconButton(onPressed: fetchFirewallData, icon: const Icon(Icons.sync)),
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
            height: constraints.maxHeight, // Ensures the background fills the screen height
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
                  minHeight: constraints.maxHeight, // Ensures the content fills the screen height
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const SizedBox(height: 16),
                    // const Padding(
                    //   padding: EdgeInsets.symmetric(vertical: 16),
                    //   child: StyledHeading('Currently Blocked IPs'),
                    // ),
                    ...blacklist.map((entry) {
                      String ifblocked = 'none';
                      for (var myentry in myBlacklist) {
                        if (myentry['blacklist_entry__capturedpacket_entry__ip'] == entry['capturedpacket_entry__ip']) {
                          ifblocked = 'blocked';
                          break;
                        }
                      }
                      return BlacklistCard(
                        entry['capturedpacket_entry__ip'] ?? 'Unknown IP',
                        entry['capturedpacket_entry__url'] ?? 'No URL',
                        ifblocked,
                        fetch: fetchFirewallData,
                      );
                    }).toList(),
                  ],
                ),
              ),
            ),
          );
        },
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