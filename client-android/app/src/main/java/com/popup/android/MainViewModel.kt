package com.popup.android

import android.app.Application
import android.content.Context
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.popup.android.crypto.CryptoManager
import com.popup.android.network.PopupSocketClient
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import org.json.JSONArray
import org.json.JSONObject
import java.security.KeyPair

/**
 * ViewModel — holds all app state and business logic.
 *
 * Android concept: ViewModel survives configuration changes (screen rotation).
 * Compose UI observes StateFlows and recomposes when values change.
 *
 * Equivalent to the useState/useRef hooks in MainScreen.js (React Native).
 */

data class ReceivedMessage(val content: String, val timestamp: String, val sender: String)

class MainViewModel(application: Application) : AndroidViewModel(application) {

    // ── SharedPreferences (equivalent to AsyncStorage) ──────

    private val prefs = application.getSharedPreferences("popup_prefs", Context.MODE_PRIVATE)

    // ── UI State ────────────────────────────────────────────

    private val _serverHost = MutableStateFlow(prefs.getString("server_host", "192.168.50.8") ?: "192.168.50.8")
    val serverHost: StateFlow<String> = _serverHost

    private val _serverPort = MutableStateFlow(prefs.getInt("server_port", 12345))
    val serverPort: StateFlow<Int> = _serverPort

    private val _isConnected = MutableStateFlow(false)
    val isConnected: StateFlow<Boolean> = _isConnected

    private val _encryptionReady = MutableStateFlow(false)
    val encryptionReady: StateFlow<Boolean> = _encryptionReady

    private val _status = MutableStateFlow("")
    val status: StateFlow<String> = _status

    private val _messages = MutableStateFlow<List<ReceivedMessage>>(emptyList())
    val messages: StateFlow<List<ReceivedMessage>> = _messages

    private val _connectedClients = MutableStateFlow<List<String>>(emptyList())
    val connectedClients: StateFlow<List<String>> = _connectedClients

    private val _showSettings = MutableStateFlow(false)
    val showSettings: StateFlow<Boolean> = _showSettings

    private val _messageInput = MutableStateFlow("")
    val messageInput: StateFlow<String> = _messageInput

    private val _fontSize = MutableStateFlow(prefs.getInt("font_size", 16))
    val fontSize: StateFlow<Int> = _fontSize

    // ── Internal state (not observed by UI) ─────────────────

    private var socketClient: PopupSocketClient? = null
    private var rsaKeyPair: KeyPair? = null
    private var aesKey: ByteArray? = null
    private var previousAesKey: ByteArray? = null

    // ── Lifecycle ───────────────────────────────────────────

    init {
        connect()
    }

    override fun onCleared() {
        super.onCleared()
        socketClient?.disconnect()
    }

    // ── Actions (called from UI) ────────────────────────────

    fun updateMessageInput(text: String) {
        _messageInput.value = text
    }

    fun toggleSettings() {
        _showSettings.value = !_showSettings.value
    }

    fun saveHost(host: String) {
        _serverHost.value = host
        prefs.edit().putString("server_host", host).apply()
        _showSettings.value = false
        reconnect()
    }

    fun saveFontSize(size: Int) {
        _fontSize.value = size
        prefs.edit().putInt("font_size", size).apply()
    }

    fun clearMessages() {
        _messages.value = emptyList()
    }

    fun reconnect() {
        disconnect()
        connect()
    }

    fun sendMessage() {
        val text = _messageInput.value.trim()
        if (text.isEmpty()) return

        if (!_isConnected.value) {
            _status.value = "Not connected to server"
            return
        }
        if (!_encryptionReady.value) {
            _status.value = "Encryption not ready, please wait..."
            return
        }

        val key = aesKey ?: return
        try {
            val encrypted = CryptoManager.aesEncrypt(key, text)
            socketClient?.send(encrypted)

            // Add own message to the chat
            val timestamp = java.text.SimpleDateFormat(
                "yyyy-MM-dd'T'HH:mm:ss", java.util.Locale.getDefault()
            ).format(java.util.Date())
            _messages.value = _messages.value + ReceivedMessage(text, timestamp, "You")

            _status.value = "Message Sent"
            _messageInput.value = ""
        } catch (e: Exception) {
            _status.value = "Failed to send: ${e.message}"
        }
    }

    // ── Connection ──────────────────────────────────────────

    private fun connect() {
        // Reset encryption state
        _encryptionReady.value = false
        aesKey = null
        previousAesKey = null
        rsaKeyPair = null
        _status.value = "Connecting..."

        val client = PopupSocketClient(viewModelScope)
        socketClient = client

        // Observe connection status
        viewModelScope.launch {
            client.isConnected.collect { connected ->
                _isConnected.value = connected
                if (connected) {
                    _status.value = "Connected, setting up encryption..."
                    initiateKeyExchange()
                }
            }
        }

        // Observe incoming messages
        viewModelScope.launch {
            client.incoming.collect { rawMessage ->
                handleRawMessage(rawMessage)
            }
        }

        // Initiate connection
        client.connect(_serverHost.value, _serverPort.value)
    }

    private fun disconnect() {
        socketClient?.disconnect()
        socketClient = null
        _isConnected.value = false
        _encryptionReady.value = false
        _connectedClients.value = emptyList()
        aesKey = null
        previousAesKey = null
        rsaKeyPair = null
    }

    // ── Key Exchange ────────────────────────────────────────

    private fun initiateKeyExchange() {
        viewModelScope.launch {
            try {
                // Generate RSA keypair (CPU-bound, but fast enough for 2048-bit)
                val keyPair = CryptoManager.generateRsaKeyPair()
                rsaKeyPair = keyPair

                // Send public key to server
                val pem = CryptoManager.getPublicKeyPem(keyPair.public)
                val keyMsg = JSONObject().apply {
                    put("type", "key_exchange")
                    put("public_key", pem)
                }
                socketClient?.send(keyMsg.toString())
                _status.value = "Key exchange in progress..."
            } catch (e: Exception) {
                _status.value = "Encryption setup failed: ${e.message}"
            }
        }
    }

    private fun handleSessionKey(data: JSONObject) {
        try {
            val encryptedKeyB64 = data.getString("encrypted_key")
            val privateKey = rsaKeyPair?.private ?: throw Exception("No RSA private key")

            val aesKeyHex = CryptoManager.rsaDecrypt(privateKey, encryptedKeyB64)
            val newKey = CryptoManager.hexToBytes(aesKeyHex)

            // Save previous key for rotation fallback
            previousAesKey = aesKey
            aesKey = newKey
            _encryptionReady.value = true
            _status.value = "Connected & encrypted"
        } catch (e: Exception) {
            _status.value = "Key exchange failed: ${e.message}"
        }
    }

    // ── Message Handling ────────────────────────────────────

    private fun handleRawMessage(rawMessage: String) {
        try {
            val json = JSONObject(rawMessage)
            val type = json.optString("type")
            val timestamp = json.optString("timestamp", "")

            when (type) {
                "status" -> {
                    val data = json.getJSONObject("data")
                    if (data.optString("code") == "200") {
                        _isConnected.value = true
                    }
                }

                "client" -> {
                    val data = json.getJSONArray("data")
                    val clients = mutableListOf<String>()
                    for (i in 0 until data.length()) {
                        clients.add(data.getString(i))
                    }
                    _connectedClients.value = clients
                }

                "msg" -> {
                    val data = json.optString("data")
                    val sender = json.optString("sender", "Unknown")
                    val currentKey = aesKey
                    if (currentKey != null && _encryptionReady.value) {
                        try {
                            val decrypted = CryptoManager.aesDecrypt(currentKey, previousAesKey, data)
                            _messages.value = _messages.value + ReceivedMessage(decrypted, timestamp, sender)
                        } catch (e: Exception) {
                            // Decryption failed — silently skip
                        }
                    }
                }

                "session_key" -> {
                    val data = json.getJSONObject("data")
                    handleSessionKey(data)
                }

                "error" -> {
                    val errorMsg = json.optString("data", "Unknown error")
                    _status.value = "Connection error: $errorMsg"
                }
            }
        } catch (e: Exception) {
            // Malformed JSON — ignore
        }
    }
}
