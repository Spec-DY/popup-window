package com.popup.android

import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.scaleIn
import androidx.compose.animation.scaleOut
import androidx.compose.foundation.background
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.Message
import androidx.compose.material.icons.automirrored.filled.Send
import androidx.compose.material.icons.automirrored.outlined.Message
import androidx.compose.material.icons.filled.Cloud
import androidx.compose.material.icons.filled.CloudOff
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.LockOpen
import androidx.compose.material.icons.filled.People
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.outlined.Home
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.nestedscroll.nestedScroll
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import java.text.SimpleDateFormat
import java.util.*

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        installSplashScreen()
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            PopupTheme {
                MainScreen()
            }
        }
    }
}

@Composable
fun PopupTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    val colorScheme = when {
        Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
            val context = LocalContext.current
            if (darkTheme) dynamicDarkColorScheme(context)
            else dynamicLightColorScheme(context)
        }
        darkTheme -> darkColorScheme()
        else -> lightColorScheme()
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography(),
        content = content
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainScreen(viewModel: MainViewModel = viewModel()) {
    val serverHost by viewModel.serverHost.collectAsState()
    val serverPort by viewModel.serverPort.collectAsState()
    val isConnected by viewModel.isConnected.collectAsState()
    val encryptionReady by viewModel.encryptionReady.collectAsState()
    val status by viewModel.status.collectAsState()
    val messages by viewModel.messages.collectAsState()
    val connectedClients by viewModel.connectedClients.collectAsState()
    val showSettings by viewModel.showSettings.collectAsState()
    val messageInput by viewModel.messageInput.collectAsState()
    val fontSize by viewModel.fontSize.collectAsState()

    var tempIP by remember { mutableStateOf(serverHost) }
    var tempFontSize by remember { mutableFloatStateOf(fontSize.toFloat()) }
    var selectedTab by remember { mutableIntStateOf(0) }

    val scrollBehavior = TopAppBarDefaults.pinnedScrollBehavior()

    // ── Settings Dialog ──────────────────────────────────

    if (showSettings) {
        AlertDialog(
            onDismissRequest = { viewModel.toggleSettings() },
            title = { Text("Settings") },
            text = {
                Column {
                    Text(
                        "Host Address:",
                        style = MaterialTheme.typography.bodyLarge,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    OutlinedTextField(
                        value = tempIP,
                        onValueChange = { tempIP = it },
                        placeholder = { Text("Enter IP address or domain") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(12.dp)
                    )
                    Spacer(modifier = Modifier.height(20.dp))
                    Text(
                        "Font Size: ${tempFontSize.toInt()}",
                        style = MaterialTheme.typography.bodyLarge,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Slider(
                        value = tempFontSize,
                        onValueChange = { tempFontSize = it },
                        valueRange = 12f..28f,
                        steps = 7,
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            },
            confirmButton = {
                Button(onClick = {
                    val newFontSize = tempFontSize.toInt()
                    viewModel.saveFontSize(newFontSize)
                    if (tempIP != serverHost) {
                        viewModel.saveHost(tempIP)
                    } else {
                        viewModel.toggleSettings()
                    }
                }) {
                    Text("Save")
                }
            },
            dismissButton = {
                TextButton(onClick = { viewModel.toggleSettings() }) {
                    Text("Cancel")
                }
            }
        )
    }

    // ── Scaffold ─────────────────────────────────────────

    Scaffold(
        modifier = Modifier.nestedScroll(scrollBehavior.nestedScrollConnection),
        topBar = {
            CenterAlignedTopAppBar(
                title = {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        // Connection indicator dot
                        Box(
                            modifier = Modifier
                                .size(8.dp)
                                .clip(CircleShape)
                                .background(
                                    if (isConnected) Color(0xFF4CAF50)
                                    else MaterialTheme.colorScheme.error
                                )
                        )
                        Text("Popup", style = MaterialTheme.typography.titleLarge)
                    }
                },
                actions = {
                    // Clear button — only on Messages tab when messages exist
                    if (selectedTab == 0 && messages.isNotEmpty()) {
                        IconButton(onClick = { viewModel.clearMessages() }) {
                            Icon(
                                Icons.Default.Delete,
                                contentDescription = "Clear messages"
                            )
                        }
                    }
                    IconButton(onClick = {
                        tempIP = serverHost
                        tempFontSize = fontSize.toFloat()
                        viewModel.toggleSettings()
                    }) {
                        Icon(Icons.Default.Settings, contentDescription = "Settings")
                    }
                },
                scrollBehavior = scrollBehavior
            )
        },
        bottomBar = {
            NavigationBar {
                NavigationBarItem(
                    selected = selectedTab == 0,
                    onClick = { selectedTab = 0 },
                    icon = {
                        BadgedBox(
                            badge = {
                                if (selectedTab != 0 && messages.isNotEmpty()) {
                                    Badge { Text("${messages.size}") }
                                }
                            }
                        ) {
                            Icon(
                                if (selectedTab == 0) Icons.AutoMirrored.Filled.Message
                                else Icons.AutoMirrored.Outlined.Message,
                                contentDescription = null
                            )
                        }
                    },
                    label = { Text("Messages") }
                )
                NavigationBarItem(
                    selected = selectedTab == 1,
                    onClick = { selectedTab = 1 },
                    icon = {
                        Icon(
                            if (selectedTab == 1) Icons.Filled.Home else Icons.Outlined.Home,
                            contentDescription = null
                        )
                    },
                    label = { Text("Status") }
                )
            }
        },
        floatingActionButton = {
            if (selectedTab == 1) {
                FloatingActionButton(
                    onClick = { viewModel.reconnect() }
                ) {
                    Icon(Icons.Default.Refresh, contentDescription = "Reconnect")
                }
            }
        }
    ) { innerPadding ->
        when (selectedTab) {
            0 -> MessagesContent(
                innerPadding = innerPadding,
                messages = messages,
                messageInput = messageInput,
                onInputChange = { viewModel.updateMessageInput(it) },
                onSend = { viewModel.sendMessage() },
                sendEnabled = isConnected && encryptionReady,
                fontSize = fontSize
            )
            1 -> StatusContent(
                innerPadding = innerPadding,
                isConnected = isConnected,
                encryptionReady = encryptionReady,
                serverHost = serverHost,
                serverPort = serverPort,
                status = status,
                connectedClients = connectedClients
            )
        }
    }
}

// ── Status Page ─────────────────────────────────────────────

@Composable
private fun StatusContent(
    innerPadding: PaddingValues,
    isConnected: Boolean,
    encryptionReady: Boolean,
    serverHost: String,
    serverPort: Int,
    status: String,
    connectedClients: List<String>
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(innerPadding)
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 16.dp, vertical = 8.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        StatusCard(
            isConnected = isConnected,
            encryptionReady = encryptionReady,
            serverHost = serverHost,
            serverPort = serverPort,
            status = status
        )

        ClientsCard(clients = connectedClients)

        Spacer(modifier = Modifier.height(72.dp))
    }
}

// ── Messages Page (Chat Style) ──────────────────────────────

@Composable
private fun MessagesContent(
    innerPadding: PaddingValues,
    messages: List<ReceivedMessage>,
    messageInput: String,
    onInputChange: (String) -> Unit,
    onSend: () -> Unit,
    sendEnabled: Boolean,
    fontSize: Int
) {
    val listState = rememberLazyListState()
    val reversedMessages = messages.asReversed()

    // Assign colors sequentially to unique senders (guarantees different senders get different colors)
    val senderColorMap = remember(messages) {
        val map = mutableMapOf<String, Int>()
        var nextColor = 0
        messages.forEach { msg ->
            if (msg.sender != "You" && msg.sender !in map) {
                map[msg.sender] = nextColor % senderColors.size
                nextColor++
            }
        }
        map
    }

    // Auto-scroll to bottom when a new message arrives
    LaunchedEffect(messages.size) {
        if (messages.isNotEmpty()) {
            listState.animateScrollToItem(0)
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(innerPadding)
            .consumeWindowInsets(innerPadding)
            .imePadding()
    ) {
        // Message list — fills all available space
        Box(modifier = Modifier.weight(1f)) {
            if (messages.isEmpty()) {
                // Empty state
                Column(
                    modifier = Modifier.fillMaxSize(),
                    verticalArrangement = Arrangement.Center,
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Icon(
                        Icons.AutoMirrored.Outlined.Message,
                        contentDescription = null,
                        modifier = Modifier.size(64.dp),
                        tint = MaterialTheme.colorScheme.outlineVariant
                    )
                    Spacer(modifier = Modifier.height(16.dp))
                    Text(
                        "No messages yet",
                        style = MaterialTheme.typography.titleMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        "Send a message to get started",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.outline
                    )
                }
            } else {
                LazyColumn(
                    state = listState,
                    reverseLayout = true,
                    modifier = Modifier.fillMaxSize(),
                    contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp)
                ) {
                    itemsIndexed(reversedMessages) { index, msg ->
                        // Group spacing: tighter within same sender, wider between different senders
                        val aboveMsg = reversedMessages.getOrNull(index + 1)
                        val isNewGroup = aboveMsg == null || aboveMsg.sender != msg.sender

                        MessageBubble(
                            msg = msg,
                            colorIndex = senderColorMap[msg.sender] ?: 0,
                            fontSize = fontSize,
                            modifier = Modifier.padding(
                                top = if (isNewGroup && aboveMsg != null) 12.dp else 2.dp
                            )
                        )
                    }
                }
            }
        }

        // Subtle divider between messages and input
        HorizontalDivider(
            color = MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.3f)
        )

        // Chat input bar at bottom
        ChatInputBar(
            messageInput = messageInput,
            onInputChange = onInputChange,
            onSend = onSend,
            enabled = sendEnabled
        )
    }
}

// ── Chat Input Bar (Google Messages Style) ──────────────────

@Composable
private fun ChatInputBar(
    messageInput: String,
    onInputChange: (String) -> Unit,
    onSend: () -> Unit,
    enabled: Boolean
) {
    Surface(
        color = MaterialTheme.colorScheme.surfaceContainer,
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 8.dp),
            verticalAlignment = Alignment.Bottom,
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // Pill-shaped text field
            TextField(
                value = messageInput,
                onValueChange = onInputChange,
                placeholder = {
                    Text(
                        "Message",
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                },
                modifier = Modifier
                    .weight(1f)
                    .heightIn(max = 120.dp),
                shape = RoundedCornerShape(24.dp),
                colors = TextFieldDefaults.colors(
                    focusedIndicatorColor = Color.Transparent,
                    unfocusedIndicatorColor = Color.Transparent,
                    disabledIndicatorColor = Color.Transparent,
                    focusedContainerColor = MaterialTheme.colorScheme.surfaceContainerHighest,
                    unfocusedContainerColor = MaterialTheme.colorScheme.surfaceContainerHigh
                ),
                maxLines = 4
            )

            // Circular send button — animates in/out
            AnimatedVisibility(
                visible = messageInput.isNotBlank(),
                enter = scaleIn(),
                exit = scaleOut()
            ) {
                FilledIconButton(
                    onClick = onSend,
                    enabled = enabled,
                    modifier = Modifier.size(48.dp)
                ) {
                    Icon(
                        Icons.AutoMirrored.Filled.Send,
                        contentDescription = "Send"
                    )
                }
            }
        }
    }
}

// ── Chat Bubble ─────────────────────────────────────────────

/** Color palette for different senders */
private val senderColors = listOf(
    Color(0xFFD1C4E9), // Light purple
    Color(0xFFB2DFDB), // Light teal
    Color(0xFFFFCCBC), // Light orange
    Color(0xFFC8E6C9), // Light green
    Color(0xFFBBDEFB), // Light blue
    Color(0xFFF8BBD0), // Light pink
)

@Composable
private fun MessageBubble(
    msg: ReceivedMessage,
    colorIndex: Int = 0,
    fontSize: Int = 16,
    modifier: Modifier = Modifier
) {
    val isOwn = msg.sender == "You"

    val bubbleColor = if (isOwn) {
        MaterialTheme.colorScheme.primaryContainer
    } else {
        senderColors[colorIndex % senderColors.size]
    }

    val textColor = if (isOwn) {
        MaterialTheme.colorScheme.onPrimaryContainer
    } else {
        Color(0xFF1C1B1F)
    }

    val bubbleShape = if (isOwn) {
        RoundedCornerShape(16.dp, 16.dp, 4.dp, 16.dp)
    } else {
        RoundedCornerShape(16.dp, 16.dp, 16.dp, 4.dp)
    }

    Row(
        modifier = modifier.fillMaxWidth(),
        horizontalArrangement = if (isOwn) Arrangement.End else Arrangement.Start
    ) {
        Surface(
            color = bubbleColor,
            shape = bubbleShape,
            modifier = Modifier.widthIn(max = 280.dp)
        ) {
            Column(
                modifier = Modifier.padding(horizontal = 12.dp, vertical = 8.dp)
            ) {
                Text(
                    text = msg.content,
                    style = MaterialTheme.typography.bodyMedium,
                    color = textColor,
                    fontSize = fontSize.sp
                )

                Text(
                    text = formatTimestamp(msg.timestamp),
                    style = MaterialTheme.typography.labelSmall,
                    color = textColor.copy(alpha = 0.5f),
                    modifier = Modifier.align(Alignment.End)
                )
            }
        }
    }
}

// ── Status Card ─────────────────────────────────────────────

@Composable
private fun StatusCard(
    isConnected: Boolean,
    encryptionReady: Boolean,
    serverHost: String,
    serverPort: Int,
    status: String
) {
    val connectionColor = if (isConnected) Color(0xFF2E7D32) else MaterialTheme.colorScheme.error

    ElevatedCard(
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Icon(
                    imageVector = if (isConnected) Icons.Default.Cloud else Icons.Default.CloudOff,
                    contentDescription = "Connection status",
                    tint = connectionColor,
                    modifier = Modifier.size(28.dp)
                )
                Column {
                    Text(
                        text = if (isConnected) "Connected" else "Disconnected",
                        style = MaterialTheme.typography.titleMedium,
                        color = connectionColor
                    )
                    Text(
                        text = "$serverHost:$serverPort",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }

            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                Icon(
                    imageVector = if (encryptionReady) Icons.Default.Lock else Icons.Default.LockOpen,
                    contentDescription = "Encryption status",
                    tint = if (encryptionReady) Color(0xFF2E7D32) else MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.size(16.dp)
                )
                Text(
                    text = if (encryptionReady) "Encrypted" else "Not encrypted",
                    style = MaterialTheme.typography.labelMedium,
                    color = if (encryptionReady) Color(0xFF2E7D32) else MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            if (status.isNotEmpty()) {
                Text(
                    text = status,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.primary
                )
            }
        }
    }
}

// ── Connected Clients Card ──────────────────────────────────

@Composable
private fun ClientsCard(clients: List<String>) {
    OutlinedCard(
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Icon(
                    Icons.Default.People,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.primary,
                    modifier = Modifier.size(20.dp)
                )
                Text(
                    text = "Clients (${clients.size})",
                    style = MaterialTheme.typography.titleSmall,
                    color = MaterialTheme.colorScheme.onSurface
                )
            }

            if (clients.isEmpty()) {
                Text(
                    text = "No other clients connected",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    fontStyle = FontStyle.Italic
                )
            } else {
                Box(modifier = Modifier.heightIn(max = 80.dp)) {
                    LazyColumn(
                        verticalArrangement = Arrangement.spacedBy(4.dp)
                    ) {
                        items(clients) { clientIP ->
                            Text(
                                text = clientIP,
                                style = MaterialTheme.typography.bodyMedium,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }
                }
            }
        }
    }
}

/** Format ISO timestamp to local time string */
private fun formatTimestamp(isoTimestamp: String): String {
    return try {
        val parser = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.getDefault())
        val date = parser.parse(isoTimestamp)
        val formatter = SimpleDateFormat("HH:mm:ss", Locale.getDefault())
        if (date != null) formatter.format(date) else isoTimestamp
    } catch (e: Exception) {
        isoTimestamp
    }
}
