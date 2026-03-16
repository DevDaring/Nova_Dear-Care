import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../providers/health_provider.dart';
import '../services/aws_sync_service.dart';
import '../env_config.dart';
import 'package:provider/provider.dart';

/// Settings Screen - worker ID configuration and app settings
class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final TextEditingController _workerIdController = TextEditingController();
  final TextEditingController _apiUrlController = TextEditingController();
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    final prefs = await SharedPreferences.getInstance();
    _workerIdController.text = prefs.getString('worker_id') ?? EnvConfig.workerId;
    _apiUrlController.text = prefs.getString('api_gateway_url') ?? EnvConfig.apiGatewayUrl;

    // Auto-save defaults on first launch
    if (prefs.getString('worker_id') == null && EnvConfig.workerId != 'YOUR_WORKER_ID') {
      await prefs.setString('worker_id', EnvConfig.workerId);
      await prefs.setString('api_gateway_url', EnvConfig.apiGatewayUrl);
    }
    setState(() => _isLoading = false);
  }

  Future<void> _saveSettings() async {
    final workerId = _workerIdController.text.trim();
    if (workerId.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Worker ID cannot be empty')),
      );
      return;
    }

    final apiUrl = _apiUrlController.text.trim();

    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('worker_id', workerId);
    if (apiUrl.isNotEmpty) {
      await prefs.setString('api_gateway_url', apiUrl);
    }

    // Reinitialize health provider with new worker ID
    if (mounted) {
      context.read<HealthProvider>().initialize(workerId: workerId);
    }

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Settings saved successfully')),
      );
    }
  }

  @override
  void dispose() {
    _workerIdController.dispose();
    _apiUrlController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                // Worker ID Section
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            const Icon(Icons.badge, color: Colors.green),
                            const SizedBox(width: 8),
                            Text(
                              'Worker Configuration',
                              style: Theme.of(context).textTheme.titleMedium,
                            ),
                          ],
                        ),
                        const SizedBox(height: 16),
                        TextField(
                          controller: _workerIdController,
                          decoration: const InputDecoration(
                            labelText: 'Worker ID',
                            hintText: 'Enter your worker ID',
                            prefixIcon: Icon(Icons.person),
                            border: OutlineInputBorder(),
                          ),
                          textCapitalization: TextCapitalization.characters,
                        ),
                        const SizedBox(height: 16),
                        TextField(
                          controller: _apiUrlController,
                          decoration: const InputDecoration(
                            labelText: 'API Gateway URL',
                            hintText: 'https://xxx.execute-api.region.amazonaws.com/prod/fitu-health',
                            prefixIcon: Icon(Icons.cloud),
                            border: OutlineInputBorder(),
                          ),
                          keyboardType: TextInputType.url,
                        ),
                        const SizedBox(height: 16),
                        ElevatedButton.icon(
                          onPressed: _saveSettings,
                          icon: const Icon(Icons.save),
                          label: const Text('Save Settings'),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),

                // About Section
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            const Icon(Icons.info_outline, color: Colors.green),
                            const SizedBox(width: 8),
                            Text(
                              'About Fit-U',
                              style: Theme.of(context).textTheme.titleMedium,
                            ),
                          ],
                        ),
                        const SizedBox(height: 16),
                        const Text('Version: 1.0.0'),
                        const SizedBox(height: 8),
                        const Text(
                          'Fit-U — Health Companion for Dear-Care AI Assistant',
                          style: TextStyle(color: Colors.grey),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),

                // Health Data Sources Info
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(Icons.sensors, color: Colors.green.shade700),
                            const SizedBox(width: 8),
                            Text(
                              'Data Sources',
                              style: Theme.of(context).textTheme.titleMedium,
                            ),
                          ],
                        ),
                        const SizedBox(height: 16),
                        _buildDataSourceItem('👣 Steps', 'Pedometer sensor'),
                        _buildDataSourceItem('📏 Distance', 'GPS location tracking'),
                        _buildDataSourceItem('⚡ Speed', 'GPS velocity data'),
                        _buildDataSourceItem('🏃 Activity', 'Motion sensor detection'),
                      ],
                    ),
                  ),
                ),
              ],
            ),
    );
  }

  Widget _buildDataSourceItem(String label, String description) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          SizedBox(
            width: 80,
            child: Text(label, style: const TextStyle(fontSize: 18)),
          ),
          Expanded(child: Text(description, style: const TextStyle(color: Colors.grey))),
        ],
      ),
    );
  }
}
