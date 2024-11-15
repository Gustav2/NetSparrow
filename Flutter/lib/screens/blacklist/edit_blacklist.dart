import 'package:flutter/material.dart';
import 'package:my_app/models/blacklist_card.dart';
import 'package:my_app/models/data_from_api.dart';
import 'package:my_app/shared/styled_text.dart';

class EditBlacklist extends StatefulWidget {
  const EditBlacklist({super.key});

  @override
  State<EditBlacklist> createState() => _HomeState();
}

class _HomeState extends State<EditBlacklist> {
  final ApiService apiService = ApiService();
  List blacklist = [];
  List myBlacklist = [];
  String ifblocked = 'none';
  Map changes = {"2.1.1.1":"https://www.youtube.com", "444.444.444.005":"http://445.dk"};

  @override
  void initState() {
    super.initState();
    fetchFirewallData();
  }


  Future<void> apply() async {
    try {
      for (var entry in changes.entries) {
        apiService.addToMyBlacklist(entry.key, entry.value);
      }
    } catch (e) {
      print("Error fetching data: $e");
    }
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
        title: const StyledTitle('Edit Blacklist'),
        leading: IconButton(onPressed: apply, icon: const Icon(Icons.sync)),
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
                      String check = 'unchecked';
                      for (var myentry in myBlacklist) {
                        if (myentry['blacklist_entry__capturedpacket_entry__ip'] == entry['capturedpacket_entry__ip']) {
                          check = 'checked';
                          break;
                        }
                      }
                      return BlacklistCard(
                        entry['capturedpacket_entry__ip'] ?? 'Unknown IP',
                        entry['capturedpacket_entry__url'] ?? 'No URL',
                        check,
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

