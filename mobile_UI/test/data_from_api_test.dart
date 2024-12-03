import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:my_app/models/data_from_api.dart';
import 'data_from_api_test.mocks.dart';

@GenerateMocks([http.Client])
void main() {
  group('ApiService - getStatus', () {
    late MockClient mockClient;
    late ApiService apiService;

    setUp(() {
      mockClient = MockClient();
      apiService = ApiService(client: mockClient);
    });

    test('returns true when the API call is successful', () async {
      // Arrange
      when(mockClient.get(
        Uri.parse('${apiService.blacklistUrl}/settings/centralblacklist/'),
        headers: {
          'Authorization': apiService.token,
          'Content-Type': 'application/json',
        },
      )).thenAnswer((_) async => http.Response('', 200));

      // Act
      final result = await apiService.getStatus();

      // Assert
      expect(result, true);
    });

    test('returns false when the API call fails', () async {
      // Arrange
      when(mockClient.get(
        Uri.parse('${apiService.blacklistUrl}/settings/centralblacklist/'),
        headers: {
          'Authorization': apiService.token,
          'Content-Type': 'application/json',
        },
      )).thenAnswer((_) async => http.Response('', 404));

      // Act
      final result = await apiService.getStatus();

      // Assert
      expect(result, false);
    });
  });
} 