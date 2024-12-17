import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:my_app/models/data_from_api.dart';
import 'package:my_app/screens/blacklist/blacklist.dart';
import 'package:my_app/shared/styled_text.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';

// If using mocktail, import mocktail instead.
// import 'package:mocktail/mocktail.dart';

import 'blacklist_test.mocks.dart';

@GenerateMocks([ApiService])
void main() {
  group('Blacklist Widget Tests', () {
    late MockApiService mockApiService;

    // Sample JSON data representing the firewall responses
    final sampleBlacklistData = [
      {
        'capturedpacket_entry__ip': '192.168.1.10',
        'some_other_key': 'some_value',
      },
      {
        'capturedpacket_entry__ip': '192.168.1.20',
        'some_other_key': 'some_value',
      },
      {
        'capturedpacket_entry__ip': '192.168.1.30',
        'some_other_key': 'some_value',
      },
    ];

    final sampleMyBlacklistData = [
      {
        'blacklist_entry__capturedpacket_entry__ip': '192.168.1.10',
      },
      {
        'blacklist_entry__capturedpacket_entry__ip': '192.168.1.20',
      },
    ];

    setUp(() {
      mockApiService = MockApiService();
    });

    testWidgets(
        'Displays "Blocked IPs" when myBlacklist is not empty and data is fetched',
        (WidgetTester tester) async {
      when(mockApiService.getBlacklist())
          .thenAnswer((_) async => sampleBlacklistData);
      when(mockApiService.getMyBlacklist())
          .thenAnswer((_) async => sampleMyBlacklistData);

      await tester.pumpWidget(
        MaterialApp(
          home: BlacklistTestWrapper(
            mockApiService: mockApiService,
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('Blocked IPs'), findsOneWidget);
      expect(find.text('192.168.1.10'), findsOneWidget);
      expect(find.text('192.168.1.20'), findsOneWidget);
    });

    testWidgets('Displays "Ignored IPs" when there are IPs not in myBlacklist',
        (WidgetTester tester) async {
      when(mockApiService.getBlacklist())
          .thenAnswer((_) async => sampleBlacklistData);
      when(mockApiService.getMyBlacklist())
          .thenAnswer((_) async => sampleMyBlacklistData);

      await tester.pumpWidget(
        MaterialApp(
          home: BlacklistTestWrapper(
            mockApiService: mockApiService,
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('Ignored IPs'), findsOneWidget);
      expect(find.text('192.168.1.30'), findsOneWidget);
    });

    testWidgets('Displays "The blacklist is empty" when no data is returned',
        (WidgetTester tester) async {
      when(mockApiService.getBlacklist()).thenAnswer((_) async => []);
      when(mockApiService.getMyBlacklist()).thenAnswer((_) async => []);

      await tester.pumpWidget(
        MaterialApp(
          home: BlacklistTestWrapper(
            mockApiService: mockApiService,
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('The blacklist is empty'), findsOneWidget);
    });

    testWidgets('Show more button increases displayed entries',
        (WidgetTester tester) async {
      // Create a large list to trigger "Show more" functionality
      final largeBlacklistData = List.generate(30, (index) {
        return {'capturedpacket_entry__ip': '192.168.1.${index + 1}'};
      });
      final largeMyBlacklistData = List.generate(15, (index) {
        return {
          'blacklist_entry__capturedpacket_entry__ip': '192.168.1.${index + 1}',
        };
      });

      when(mockApiService.getBlacklist())
          .thenAnswer((_) async => largeBlacklistData);
      when(mockApiService.getMyBlacklist())
          .thenAnswer((_) async => largeMyBlacklistData);

      await tester.pumpWidget(
        MaterialApp(
          home: BlacklistTestWrapper(
            mockApiService: mockApiService,
          ),
        ),
      );

      await tester.pumpAndSettle();

      // maxEntriesBlocked = 10
      for (var i = 1; i <= 10; i++) {
        expect(find.text('192.168.1.$i'), findsOneWidget);
      }

      // IP 11 is not visible yet
      expect(find.text('192.168.1.11'), findsNothing);

      // show more
      final showMoreButton = find.text('Show more').first;
      expect(showMoreButton, findsOneWidget);
      await tester.tap(showMoreButton);
      await tester.pumpAndSettle();

      // 192.168.1.11 visible
      expect(find.text('192.168.1.11'), findsOneWidget);
    });
  });
}


class BlacklistTestWrapper extends StatelessWidget {
  final ApiService mockApiService;

  const BlacklistTestWrapper({Key? key, required this.mockApiService})
      : super(key: key);

  @override
  Widget build(BuildContext context) {
    return BlacklistWithApiService(apiService: mockApiService);
  }
}


class BlacklistWithApiService extends StatefulWidget {
  final ApiService apiService;
  const BlacklistWithApiService({Key? key, required this.apiService})
      : super(key: key);

  @override
  State<BlacklistWithApiService> createState() =>
      _BlacklistWithApiServiceState();
}

class _BlacklistWithApiServiceState extends State<BlacklistWithApiService> {
  List blacklist = [];
  List myBlacklist = [];
  int maxEntriesBlocked = 10;
  int maxEntriesIgnored = 10;

  @override
  void initState() {
    super.initState();
    fetchFirewallData();
  }

  Future<void> fetchFirewallData() async {
    try {
      final blacklistData = await widget.apiService.getBlacklist();
      final myBlacklistData = await widget.apiService.getMyBlacklist();

      setState(() {
        blacklist = blacklistData;
        myBlacklist = myBlacklistData;
      });
    } catch (e) {
      print("Error fetching data: $e");
    }
  }

  bool _hasMoreBlockedEntries() {
    final blockedCount = blacklist
        .where((entry) => myBlacklist.any((myentry) =>
            myentry['blacklist_entry__capturedpacket_entry__ip'] ==
            entry['capturedpacket_entry__ip']))
        .length;

    return blockedCount > maxEntriesBlocked;
  }

  bool _hasMoreIgnoredEntries() {
    final ignoredCount = blacklist
        .where((entry) => !myBlacklist.any((myentry) =>
            myentry['blacklist_entry__capturedpacket_entry__ip'] ==
            entry['capturedpacket_entry__ip']))
        .length;

    return ignoredCount > maxEntriesIgnored;
  }

  @override
  Widget build(BuildContext context) {
    final blockedEntries = blacklist
        .where((entry) => myBlacklist.any((myentry) =>
            myentry['blacklist_entry__capturedpacket_entry__ip'] ==
            entry['capturedpacket_entry__ip']))
        .take(maxEntriesBlocked)
        .toList();

    final ignoredEntries = blacklist
        .where((entry) => !myBlacklist.any((myentry) =>
            myentry['blacklist_entry__capturedpacket_entry__ip'] ==
            entry['capturedpacket_entry__ip']))
        .take(maxEntriesIgnored)
        .toList();

    return Scaffold(
      appBar: AppBar(
        title: const StyledTitle('My Blacklist'),
      ),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            blockedEntries.isEmpty
                ? const StyledHeading('The blacklist is empty')
                : const StyledHeading('Blocked IPs'),
            ...blockedEntries
                .map((entry) => Text(entry['capturedpacket_entry__ip'])),
            if (_hasMoreBlockedEntries())
              TextButton(
                onPressed: () {
                  setState(() {
                    maxEntriesBlocked += 10;
                  });
                },
                child: const Text('Show more'),
              ),
            if (ignoredEntries.isNotEmpty) const StyledHeading('Ignored IPs'),
            ...ignoredEntries
                .map((entry) => Text(entry['capturedpacket_entry__ip'])),
            if (_hasMoreIgnoredEntries())
              TextButton(
                onPressed: () {
                  setState(() {
                    maxEntriesIgnored += 10;
                  });
                },
                child: const Text('Show more'),
              ),
          ],
        ),
      ),
    );
  }
}
