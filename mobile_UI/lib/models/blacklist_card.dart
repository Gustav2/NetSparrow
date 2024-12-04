import 'package:flutter/material.dart';
import 'package:my_app/models/data_from_api.dart';
import 'package:my_app/shared/styled_text.dart';

class BlacklistCard extends StatelessWidget {
  BlacklistCard(
    this.ip,
    this.url,
    this.state,
    {required this.fetch, super.key});

  final ApiService apiService = ApiService();
  final String ip;
  final String url;
  final String state;
  final VoidCallback fetch;

  @override
  Widget build(BuildContext context) {
    return Card(
      color: state == 'none' ? const Color.fromARGB(255, 126, 126, 126).withOpacity(0.1) : Colors.white,
      surfaceTintColor: state == 'none' ?  Colors.white : Colors.transparent,
      
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        child: Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                    SizedBox(
                      width: MediaQuery.of(context).size.width * 0.7,
                      child: state == 'none' 
                        ? StyledGreyHeading(url) 
                        : StyledHeading(url),
                    ),
                    const SizedBox(height: 8),
                    SizedBox(
                      width: MediaQuery.of(context).size.width * 0.7,
                      child: state == 'none' 
                        ? StyledGreyText(ip) 
                        : StyledText(ip),
                    ),
                    const SizedBox(height: 8),
                ],
              ),
              const Expanded(child: SizedBox()),
              if (state == 'checked') IconButton(onPressed: () async {await removeFromBlacklist(); fetch();}, icon: const Icon(Icons.remove, color: Color.fromARGB(255, 71, 71, 71), size: 32,)),
              if (state == 'unchecked') IconButton(onPressed: () async {await addToBlacklist(); fetch();}, icon: const Icon(Icons.add, color: Color.fromARGB(255, 71, 71, 71), size: 32,)),
            ],
          ),
        ),
      )
    );
  }

  Future<void> addToBlacklist() async {
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
  }

  Future<void> removeFromBlacklist() async{
    if (url == 'No URL') {
      print('test4');
      await apiService.removeFromMyBlacklist(ip, 'null');
    } else if (ip == 'Unknown IP') {
      print('test5');
      await apiService.removeFromMyBlacklist('null', url);
    } else {
      print('test6');
      await apiService.removeFromMyBlacklist(ip, url);
    }
  }
}