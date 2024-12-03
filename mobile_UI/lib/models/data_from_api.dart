import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:my_app/models/keys.dart';

// The Api Service class is responsible for fetching data from the API.
class ApiService {
  final http.Client client;

  ApiService({http.Client? client}) : client = client ?? http.Client();
  final String blacklistUrl = blacklisturl; // url to the blacklist API
  final String token = blacklistToken; // token for the blacklist API
  final String baseUrl = piurl; // url to the pi API
  final int key = apiKey; // api key for the pi API

  // Fetches the firewall status from the API. reuturns true if the system i running as expected.
  Future<bool> getStatus() async {
    final response = await client.get(
      Uri.parse("$blacklistUrl/settings/centralblacklist/"), // sends a get request to the centralblacklist API
      headers: {
        'Authorization': token, // includes the token in the header
        'Content-Type': 'application/json',
      },
    );

    if (response.statusCode == 200) {
      return true; // if the response is successful, return true
    } else {
      return false; // if the response is not successful, return false
    }
  }

  Future<List<Map<String, dynamic>>> getBlacklist() async { // gets the central blacklist from the API
    final response = await http.get(
      Uri.parse("$blacklistUrl/settings/centralblacklist/"),
      headers: {
        'Authorization': token,
        'Content-Type': 'application/json',
      },
    );

    if (response.statusCode == 200) {
      Map<String, dynamic> data = jsonDecode(response.body); // decodes the response body to a map

      if (data['central_blacklist'] is List) { // checks if the central_blacklist is a list
        List<dynamic> blacklistList = data['central_blacklist']; // gets the central_blacklist

        return blacklistList // returns the central_blacklist as a list of maps, and sets the ip and url to 'Unknown IP' and 'No URL' if they are null
            .map<Map<String, dynamic>>((item) => {
                  'capturedpacket_entry__ip':
                      item['capturedpacket_entry__ip'] ??
                          'Unknown IP', 
                  'capturedpacket_entry__url':
                      item['capturedpacket_entry__url'] ??
                          'No URL',
                })
            .toList();
      } else {
        throw Exception(
            "Invalid data format: 'central_blacklist' not found or not a list."); // if the central_blacklist is not a list, throw an exception
      }
    } else {
      throw Exception("Failed to load log ${response.body}"); // if the response is not successful, throw an exception
    }
  }

  Future<List<Map<String, dynamic>>> getMyBlacklist() async { // gets the user's blacklist from the API
    final response = await http.get(
      Uri.parse("$blacklistUrl/settings/myblacklist/"),
      headers: {
        'Authorization': token,
        'Content-Type': 'application/json',
      },
    );

    if (response.statusCode == 200) {
      Map<String, dynamic> data = jsonDecode(response.body);

      if (data['myblacklists'] is List) {
        List<dynamic> blacklistList = data['myblacklists'];

        return blacklistList
            .map<Map<String, dynamic>>((item) => {
                  'blacklist_entry__capturedpacket_entry__ip':
                      item['blacklist_entry__capturedpacket_entry__ip'] ??
                          'Unknown IP',
                  'blacklist_entry__capturedpacket_entry__url':
                      item['blacklist_entry__capturedpacket_entry__url'] ??
                          'No URL',
                })
            .toList();
      } else {
        throw Exception(
            "Invalid data format: 'central_blacklist' not found or not a list.");
      }
    } else {
      throw Exception("Failed to load log");
    }
  }

  Future<void> addToMyBlacklist(String ip, String url) async { // posts an entry to the user's blacklist from the central blacklist
    final response = await http.post(
      Uri.parse("$blacklistUrl/settings/add_to_myblacklist/"),
      headers: {
        'Authorization': token,
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'ip': ip,
        'url': url == 'null' ? null : url,
      }), // removes the url if it is null
    );

    if (response.statusCode == 200) {
      print("Entry added successfully");
    } else {
      throw Exception("Failed to add entry to blacklist");
    }
  }

  Future<void> removeFromMyBlacklist(String ip, String url) async { // removes an entry from the user's blacklist
    final response = await http.delete( // sends a delete request to the API
      Uri.parse("$blacklistUrl/settings/remove_from_myblacklist/"),
      headers: {
        'Authorization': token,
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'ip': ip == 'null' ? null : ip,
        'url': url == 'null' ? null : url,
      }), // removes the ip and url if they are null
    );

    if (response.statusCode == 200) {
      print("Entry added successfully");
    } else {
      throw Exception("Failed to add entry to blacklist");
    }
  }

  Future<void> postSettings(Map<String, dynamic> settings) async { // updates the users settings
    final response = await http.post(
      Uri.parse("$blacklistUrl/api/settings/update/"),
      headers: {
        'Authorization': token,
        'Content-Type': 'application/json',
      },
      body: jsonEncode(settings),
    );

    if (response.statusCode == 200) {
      print("Settings updated successfully");
    } else {
      throw Exception("Failed to update settings");
    }
  }

  Future<Map<String, dynamic>> getSettings() async { // gets the users current settings
    final response = await http.get(
      Uri.parse("$blacklistUrl/api/settings/get/"),
      headers: {
        'Authorization': token,
        'Content-Type': 'application/json',
      },
    );

    if (response.statusCode == 200) {
      Map<String, dynamic> data = jsonDecode(response.body);

      Map<String, dynamic> modifiedData = {};
      data.forEach((key, value) {
        String newKey = key.replaceAll('_', ' ').split(' ').map((word) => word[0].toUpperCase() + word.substring(1).toLowerCase()).join(' ');
        newKey = newKey[0].toUpperCase() + newKey.substring(1).toLowerCase();
        modifiedData[newKey] = value; // formats the settings to be more readable in the application
      });
      return modifiedData;
    } else {
      throw Exception("Failed to load settings");
    }
  }



  // below is deprecated code that was used for previous versions of the application
  Future<int> getBlockedPackets() async {
    final response = await http.get(
      Uri.parse("$baseUrl/blocked_packets"),
      headers: {
        'x-api-key': '$key',
      },
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return data['blocked_packets'];
    } else {
      throw Exception("Failed to load blocked packets count");
    }
  }

  Future<int> getLatestSpeed() async {
    final response = await http.get(
      Uri.parse("$baseUrl/latest_speed"),
      headers: {
        'x-api-key': '$key',
      },
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return data['speed'];
    } else {
      throw Exception("Failed to load latest speed");
    }
  }

  Future<int> getLatestLatency() async {
    final response = await http.get(
      Uri.parse("$baseUrl/latest_latency"),
      headers: {
        'x-api-key': '$key',
      },
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return data['latency'];
    } else {
      throw Exception("Failed to load latest speed");
    }
  }

  Future<List> getLogList() async {
    final response = await http.get(
      Uri.parse("$baseUrl/log"),
      headers: {
        'x-api-key': '$key',
      },
    );

    if (response.statusCode == 200) {
      List<dynamic> logList = jsonDecode(response.body);
      List<int> latencies =
          logList.map((item) => item['latency'] as int).toList();
      List<int> speeds = logList.map((item) => item['speed'] as int).toList();
      List<String> timestamps =
          logList.map((item) => item['timestamp'] as String).toList();

      List<String> times = timestamps.map((timestamp) {
        return timestamp.split(' ')[4];
      }).toList();

      return List.generate(
          logList.length,
          (index) => {
                'latency': latencies[index],
                'speed': speeds[index],
                'timestamp': times[index],
              });
    } else {
      throw Exception("Failed to load log");
    }
  }
}