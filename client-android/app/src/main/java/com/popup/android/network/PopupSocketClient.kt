package com.popup.android.network

import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.PrintWriter
import java.net.Socket

/**
 * TCP socket client using Kotlin Coroutines.
 *
 * Key Android concepts demonstrated:
 * - Dispatchers.IO: offloads blocking I/O to a background thread pool
 * - SharedFlow: emits received data to collectors (ViewModel)
 * - StateFlow: observable connection status
 * - Structured concurrency: all coroutines cancel when scope is cancelled
 *
 * Equivalent to TcpSocket.createConnection() in the React Native client.
 */
class PopupSocketClient(private val scope: CoroutineScope) {

    private var socket: Socket? = null
    private var writer: PrintWriter? = null
    private var readJob: Job? = null

    /** Emits raw data strings received from the server */
    private val _incoming = MutableSharedFlow<String>(extraBufferCapacity = 64)
    val incoming: SharedFlow<String> = _incoming

    /** Connection status */
    private val _isConnected = MutableStateFlow(false)
    val isConnected: StateFlow<Boolean> = _isConnected

    /**
     * Connect to the server and start reading.
     * Runs entirely on IO dispatcher — safe to call from main thread.
     */
    fun connect(host: String, port: Int) {
        // Cancel any existing connection
        disconnect()

        readJob = scope.launch(Dispatchers.IO) {
            try {
                val sock = Socket(host, port)
                socket = sock
                writer = PrintWriter(sock.getOutputStream(), true)
                _isConnected.value = true

                // Read loop — blocks on readLine(), runs in IO thread
                val reader = BufferedReader(InputStreamReader(sock.getInputStream()))
                val buffer = CharArray(4096)

                while (isActive) {
                    val bytesRead = reader.read(buffer)
                    if (bytesRead == -1) break // Server closed connection

                    val data = String(buffer, 0, bytesRead)
                    // Split concatenated JSON messages (same as other clients)
                    splitMessages(data).forEach { msg ->
                        _incoming.emit(msg)
                    }
                }
            } catch (e: Exception) {
                // Connection failed or lost
                if (isActive) {
                    // Emit error as a special message the ViewModel can handle
                    _incoming.emit("{\"type\":\"error\",\"data\":\"${e.message}\"}")
                }
            } finally {
                cleanup()
            }
        }
    }

    /** Send data to server. Safe to call from any thread. */
    fun send(data: String) {
        scope.launch(Dispatchers.IO) {
            try {
                writer?.println(data)
                writer?.flush()
            } catch (e: Exception) {
                _incoming.emit("{\"type\":\"error\",\"data\":\"Send failed: ${e.message}\"}")
            }
        }
    }

    /** Close the connection */
    fun disconnect() {
        readJob?.cancel()
        readJob = null
        cleanup()
    }

    private fun cleanup() {
        try {
            writer?.close()
            socket?.close()
        } catch (_: Exception) {
        }
        writer = null
        socket = null
        _isConnected.value = false
    }

    /**
     * Split concatenated JSON messages on }{ boundary.
     * TCP can deliver multiple JSON objects in one read:
     * e.g. {"type":"status",...}{"type":"client",...}
     */
    private fun splitMessages(data: String): List<String> {
        return data.replace("}{", "}\n{")
            .split("\n")
            .filter { it.isNotBlank() }
    }
}
