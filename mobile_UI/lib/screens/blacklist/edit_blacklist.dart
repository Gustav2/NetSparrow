import 'package:flutter/material.dart';
import 'package:my_app/models/blacklist_card.dart';
import 'package:my_app/models/data_from_api.dart';
import 'package:my_app/screens/blacklist/blacklist_menu_bar.dart';
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
  bool loading = false;
  String filter = '';

  @override
  void initState() {
    super.initState();
    fetchFirewallData();
  }

  Future<void> setLoading(bool value) async {
    setState(() {
      loading = value;
    });

    if (loading) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          elevation: 0,
          backgroundColor: Colors.transparent,
          content: Container(
            padding: EdgeInsets.all(16),
            child: Center(
                child: Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(16),
                      boxShadow: const [
                        BoxShadow(
                          color: Colors.black12,
                          blurRadius: 10,
                          spreadRadius: 5,
                          offset: Offset(0, 0),
                        ),
                      ],
                    ),
                    child: const CircularProgressIndicator(
                      valueColor: AlwaysStoppedAnimation<Color>(Colors.black),
                    ))),
          ),
          duration: Duration(days: 1),
        ),
      );
    } else {
      ScaffoldMessenger.of(context).hideCurrentSnackBar();
    }
  }

  Future<void> addAll() async {
    await setLoading(true);

    for (var entry in blacklist) {
      String ip = entry['capturedpacket_entry__ip'] ?? 'Unknown IP';
      String url = entry['capturedpacket_entry__url'] ?? 'No URL';

      try {
        if (url == 'No URL') {
          print('test1');
          await apiService.addToMyBlacklist(ip, 'null');
        } else if (ip == 'Unknown IP') {
          print('test2');
          await apiService.addToMyBlacklist('null', url);
        } else {
          print('test3');
          await apiService.addToMyBlacklist(ip, url);
        }
      } catch (e) {
        print("Error adding to blacklist: $e");
      }
    }

    await setLoading(false);

    print('done');
    fetchFirewallData();
  }

  Future<void> removeAll() async {
    await setLoading(true);

    for (var entry in myBlacklist) {
      String ip =
          entry['blacklist_entry__capturedpacket_entry__ip'] ?? 'Unknown IP';
      String url =
          entry['blacklist_entry__capturedpacket_entry__url'] ?? 'No URL';

      try {
        if (url == 'No URL') {
          await apiService.removeFromMyBlacklist(ip, 'null');
        } else if (ip == 'Unknown IP') {
          await apiService.removeFromMyBlacklist('null', url);
        } else {
          await apiService.removeFromMyBlacklist(ip, url);
        }
      } catch (e) {
        print("Error removing from blacklist: $e");
      }
    }

    await setLoading(false);
    print('done');
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
      setState(() {
        print("Error: ${e.toString()}");
      });
      print("Error fetching data: $e");
    }
  }

  List<Widget> displayCards(String filter) {
    return blacklist.where((entry) {
      String ip =
          (entry['capturedpacket_entry__ip'] ?? 'Unknown IP').toLowerCase();
      String url =
          (entry['capturedpacket_entry__url'] ?? 'No URL').toLowerCase();
      return ip.contains(filter) || url.contains(filter);
    }).map((entry) {
      String check = 'unchecked';
      for (var myentry in myBlacklist) {
        if (myentry['blacklist_entry__capturedpacket_entry__ip'] ==
            entry['capturedpacket_entry__ip']) {
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
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const StyledTitle('Edit Blacklist'),
        leading: IconButton(
            onPressed: fetchFirewallData, icon: const Icon(Icons.sync)),
        actions: [
          BlacklistMenu(addAll: addAll, removeAll: removeAll),
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
                    const SizedBox(height: 16),
                    Row(children: [Container()]),
                    Padding(
                      padding: const EdgeInsets.only(
                          bottom: 16, left: 16, right: 16),
                      child: SearchBar(
                        surfaceTintColor:
                            const WidgetStatePropertyAll(Colors.transparent),
                        backgroundColor:
                            const WidgetStatePropertyAll(Colors.white),
                        hintText: 'Search for IP or URL',
                        onChanged: (value) {
                          setState(() {
                            filter = value.toLowerCase();
                          });
                        },
                      ),
                    ),
                    ...displayCards(filter),
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
