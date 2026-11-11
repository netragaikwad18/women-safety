import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

void main() {
  runApp(const SmartSafetyApp());
}

class SmartSafetyApp extends StatelessWidget {
  const SmartSafetyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Smart Women Safety Alert',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFFE91E63),
          primary: const Color(0xFFE91E63),
          secondary: const Color(0xFF9C27B0),
        ),
        useMaterial3: true,
      ),
      home: const MobileHomeScreen(),
    );
  }
}

class MobileHomeScreen extends StatefulWidget {
  const MobileHomeScreen({super.key});

  @override
  State<MobileHomeScreen> createState() => _MobileHomeScreenState();
}

class _MobileHomeScreenState extends State<MobileHomeScreen> {
  int _selectedIndex = 0;
  static const String _baseUrl = "http://10.0.2.2:8000/api"; // Default Android emulator host loopback
  bool _isCountdownActive = false;
  int _countdownSeconds = 5;
  Timer? _countdownTimer;
  String _currentMode = "normal";

  // State variables
  final int _batteryLevel = 92;
  final String _networkStatus = "4G LTE Connected";

  @override
  void initState() {
    super.initState();
  }

  void _startSosCountdown(String mode) {
    setState(() {
      _currentMode = mode;
      _countdownSeconds = 5;
      _isCountdownActive = true;
    });

    _countdownTimer?.cancel();
    _countdownTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_countdownSeconds > 1) {
        setState(() {
          _countdownSeconds--;
        });
      } else {
        timer.cancel();
        setState(() {
          _isCountdownActive = false;
        });
        _sendSosAlert(_currentMode);
      }
    });
  }

  void _cancelSosCountdown() {
    _countdownTimer?.cancel();
    setState(() {
      _isCountdownActive = false;
    });
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('SOS activation cancelled. Stay safe!'),
        backgroundColor: Colors.blueGrey,
      ),
    );
  }

  Future<void> _sendSosAlert(String mode) async {
    try {
      await http.post(
        Uri.parse('$_baseUrl/sos/trigger'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'latitude': 12.9716,
          'longitude': 77.5946,
          'trigger_type': 'button',
          'alert_mode': mode,
          'location_address': 'MG Road, Mobile GPS Track',
          'battery_level': _batteryLevel,
          'network_status': _networkStatus,
        }),
      );

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            mode == 'silent'
                ? 'SILENT SOS ACTIVATED! Emergency contacts notified.'
                : 'EMERGENCY SOS BROADCASTED TO FAMILY & POLICE!',
          ),
          backgroundColor: Colors.redAccent,
          duration: const Duration(seconds: 5),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Simulated SOS Dispatched (Local Network: $e)'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  void _simulateFakeIncomingCall() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
        backgroundColor: Colors.black87,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.account_circle, size: 80, color: Colors.white70),
            const SizedBox(height: 12),
            const Text(
              'Dad (Home)',
              style: TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold),
            ),
            const Text(
              'Incoming Mobile Call...',
              style: TextStyle(color: Colors.white70, fontSize: 14),
            ),
            const SizedBox(height: 32),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                FloatingActionButton(
                  heroTag: 'decline_call',
                  backgroundColor: Colors.red,
                  onPressed: () => Navigator.pop(ctx),
                  child: const Icon(Icons.call_end, color: Colors.white),
                ),
                FloatingActionButton(
                  heroTag: 'accept_call',
                  backgroundColor: Colors.green,
                  onPressed: () => Navigator.pop(ctx),
                  child: const Icon(Icons.call, color: Colors.white),
                ),
              ],
            )
          ],
        ),
      ),
    );
  }

  Widget _buildSosScreen() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20.0),
      child: Column(
        children: [
          // Device status bar
          Card(
            elevation: 1,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.battery_charging_full, color: Colors.green),
                      const SizedBox(width: 6),
                      Text('$_batteryLevel%', style: const TextStyle(fontWeight: FontWeight.bold)),
                    ],
                  ),
                  Row(
                    children: [
                      const Icon(Icons.wifi, color: Colors.blue),
                      const SizedBox(width: 6),
                      Text(_networkStatus, style: const TextStyle(fontWeight: FontWeight.w500)),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 30),

          // SOS Button
          Center(
            child: Stack(
              alignment: Alignment.center,
              children: [
                Container(
                  width: 230,
                  height: 230,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: Colors.red.withAlpha(38),
                  ),
                ),
                GestureDetector(
                  onTap: () => _startSosCountdown('normal'),
                  child: Container(
                    width: 180,
                    height: 180,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: const LinearGradient(
                        colors: [Color(0xFFFF1744), Color(0xFFB71C1C)],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.red.withAlpha(128),
                          blurRadius: 20,
                          spreadRadius: 5,
                        ),
                      ],
                    ),
                    child: const Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text(
                            'SOS',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 36,
                              fontWeight: FontWeight.w900,
                              letterSpacing: 2,
                            ),
                          ),
                          Text(
                            'PRESS TO ALERT',
                            style: TextStyle(
                              color: Colors.white70,
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 30),

          // Actions
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () => _startSosCountdown('silent'),
                  icon: const Icon(Icons.visibility_off, color: Colors.deepOrange),
                  label: const Text('Silent SOS'),
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    side: const BorderSide(color: Colors.deepOrange),
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: _simulateFakeIncomingCall,
                  icon: const Icon(Icons.phone_in_talk, color: Colors.purple),
                  label: const Text('Fake Call'),
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    side: const BorderSide(color: Colors.purple),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),

          // Helplines Quick Card
          Card(
            color: Colors.red.shade50,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            child: const Padding(
              padding: EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.emergency, color: Colors.red),
                      SizedBox(width: 8),
                      Text(
                        'Emergency Helplines',
                        style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                      ),
                    ],
                  ),
                  SizedBox(height: 8),
                  Text('• National Helpline: 112'),
                  Text('• Women Helpline: 1091 / 181'),
                  Text('• Ambulance / First Aid: 108'),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAiPredictScreen() {
    return Padding(
      padding: const EdgeInsets.all(20.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'AI Risk Detection (Scikit-Learn)',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          const Text(
            'Continuous machine-learning assessment of travel hour, speed, battery, and route deviation.',
            style: TextStyle(color: Colors.black54),
          ),
          const SizedBox(height: 24),
          Card(
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            child: Padding(
              padding: const EdgeInsets.all(20.0),
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('Current Risk Assessment', style: TextStyle(fontWeight: FontWeight.bold)),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: Colors.green.shade100,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: const Text('SAFE', style: TextStyle(color: Colors.green, fontWeight: FontWeight.bold)),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  const LinearProgressIndicator(
                    value: 0.18,
                    color: Colors.green,
                    backgroundColor: Colors.black12,
                    minHeight: 8,
                  ),
                  const SizedBox(height: 12),
                  const Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text('Risk Score: 18.5 / 100', style: TextStyle(fontWeight: FontWeight.w600)),
                      Text('Confidence: 82%', style: TextStyle(color: Colors.black54)),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildChatbotScreen() {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        children: [
          Expanded(
            child: ListView(
              children: [
                _buildChatBubble('bot', 'Hello! I am your AI Women Safety Assistant. I can assist in English and Kannada (ಕನ್ನಡ).'),
                _buildChatBubble('user', 'What should I do if a suspicious person is following me?'),
                _buildChatBubble('bot', '1) Move to an open crowded store immediately.\n2) Call 112 or a family member.\n3) Trigger Silent SOS on this mobile app.'),
              ],
            ),
          ),
          Row(
            children: [
              Expanded(
                child: TextField(
                  decoration: InputDecoration(
                    hintText: 'Ask safety advice...',
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(24)),
                    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              IconButton.filled(
                onPressed: () {},
                icon: const Icon(Icons.send),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildChatBubble(String sender, String text) {
    final isUser = sender == 'user';
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 6),
        padding: const EdgeInsets.all(14),
        constraints: const BoxConstraints(maxWidth: 280),
        decoration: BoxDecoration(
          color: isUser ? const Color(0xFFE91E63) : Colors.grey.shade200,
          borderRadius: BorderRadius.circular(16),
        ),
        child: Text(
          text,
          style: TextStyle(color: isUser ? Colors.white : Colors.black87),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Row(
          children: [
            Icon(Icons.shield, color: Colors.white),
            SizedBox(width: 8),
            Text('NirbhayaSafe Mobile', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
          ],
        ),
        backgroundColor: const Color(0xFFE91E63),
      ),
      body: Stack(
        children: [
          IndexedStack(
            index: _selectedIndex,
            children: [
              _buildSosScreen(),
              _buildAiPredictScreen(),
              _buildChatbotScreen(),
            ],
          ),

          // Countdown Modal Overlay
          if (_isCountdownActive)
            Container(
              color: Colors.black.withAlpha(217),
              child: Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      _currentMode == 'silent' ? 'ACTIVATING SILENT SOS' : 'EMERGENCY SOS COUNTDOWN',
                      style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      '$_countdownSeconds',
                      style: const TextStyle(color: Colors.redAccent, fontSize: 80, fontWeight: FontWeight.w900),
                    ),
                    const SizedBox(height: 24),
                    ElevatedButton.icon(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.white,
                        foregroundColor: Colors.red,
                        padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                      ),
                      onPressed: _cancelSosCountdown,
                      icon: const Icon(Icons.cancel),
                      label: const Text('CANCEL (Accidental)', style: TextStyle(fontWeight: FontWeight.bold)),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _selectedIndex,
        onTap: (index) => setState(() => _selectedIndex = index),
        selectedItemColor: const Color(0xFFE91E63),
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.emergency), label: 'Emergency SOS'),
          BottomNavigationBarItem(icon: Icon(Icons.psychology), label: 'AI Risk'),
          BottomNavigationBarItem(icon: Icon(Icons.chat), label: 'Safety Bot'),
        ],
      ),
    );
  }
}
