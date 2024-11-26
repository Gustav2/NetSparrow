import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:my_app/models/keys.dart';

class ApiService {
  final String blacklistUrl = blacklistIp;
  final String baseUrl = ip;
  final int key = apiKey;
  final String token = blacklistToken;

  Future<Map<String, dynamic>> getStatus() async {
    final response = await http.get(
      Uri.parse("$baseUrl/status"),
      headers: {
        'x-api-key': '$key',
      },
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception("Failed to load firewall status");
    }
  }

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

  Future<List<Map<String, dynamic>>> getBlacklist() async {
    final response = await http.get(
      Uri.parse("$blacklistUrl/settings/centralblacklist/"),
      headers: {
        'Authorization': token,
        'Content-Type': 'application/json',
      },
    );

    if (response.statusCode == 200) {
      Map<String, dynamic> data = jsonDecode(response.body);

      if (data['central_blacklist'] is List) {
        List<dynamic> blacklistList = data['central_blacklist'];

        return blacklistList
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
            "Invalid data format: 'central_blacklist' not found or not a list.");
      }
    } else {
      throw Exception("Failed to load log ${response.body}");
    }
  }

  Future<List<Map<String, dynamic>>> getMyBlacklist() async {
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

  Future<void> addToMyBlacklist(String ip, String url) async {
    final response = await http.post(
      Uri.parse("$blacklistUrl/settings/add_to_myblacklist/"),
      headers: {
        'Authorization': token,
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'ip': ip,
        'url': url == 'null' ? null : url,
      }),
    );

    if (response.statusCode == 200) {
      print("Entry added successfully");
    } else {
      throw Exception("Failed to add entry to blacklist");
    }
  }

  Future<void> removeFromMyBlacklist(String ip, String url) async {
    final response = await http.delete(
      Uri.parse("$blacklistUrl/settings/remove_from_myblacklist/"),
      headers: {
        'Authorization': token,
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'ip': ip == 'null' ? null : ip,
        'url': url == 'null' ? null : url,
      }),
    );

    if (response.statusCode == 200) {
      print("Entry added successfully");
    } else {
      throw Exception("Failed to add entry to blacklist");
    }
  }
}
