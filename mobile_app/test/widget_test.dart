import 'package:flutter_test/flutter_test.dart';
import 'package:smart_safety_mobile/main.dart';

void main() {
  testWidgets('SmartSafetyApp smoke test and SOS button presence', (WidgetTester tester) async {
    await tester.pumpWidget(const SmartSafetyApp());

    // Verify Title and SOS button presence
    expect(find.text('NirbhayaSafe Mobile'), findsOneWidget);
    expect(find.text('SOS'), findsOneWidget);
    expect(find.text('PRESS TO ALERT'), findsOneWidget);
  });
}
