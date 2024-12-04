import 'dart:io';

class ReverseLookup {

  const ReverseLookup({required this.ip});

  final String ip;

  Future<String> resolveIpToDomain(String ipAddress) async {
    try {
      final internetAddress = InternetAddress.tryParse(ipAddress);
      if (internetAddress == null) {
        throw const FormatException('Invalid IP address format');
      }

      final host = await internetAddress.reverse();
      return host.host;
    } catch (e) {
      return "No URL found";
    }
  }
}

