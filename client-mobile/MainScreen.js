import React, { useState, useEffect } from "react";
import {
  View,
  TextInput,
  Text,
  Pressable,
  ScrollView,
  Modal,
  Alert,
} from "react-native";
import TcpSocket from "react-native-tcp-socket";
import FontAwesome from "@expo/vector-icons/FontAwesome";
import Entypo from "@expo/vector-icons/Entypo";
import Animated, {
  useAnimatedStyle,
  withTiming,
  withRepeat,
  useSharedValue,
} from "react-native-reanimated";
import FontAwesome6 from "@expo/vector-icons/FontAwesome6";
import AsyncStorage from "@react-native-async-storage/async-storage";

export default function MainScreen() {
  const [message, setMessage] = useState("");
  const [status, setStatus] = useState("");
  const [client, setClient] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [receivedMessages, setReceivedMessages] = useState([]);
  const [connectedClients, setConnectedClients] = useState([]);
  const [showSettings, setShowSettings] = useState(false);
  const rotation = useSharedValue(0);

  const [serverConfig, setServerConfig] = useState({
    host: "192.168.50.8",
    port: 12345,
  });

  // temporary state for settings input
  const [tempHost, setTempHost] = useState(serverConfig.host);
  const [tempPort, setTempPort] = useState(serverConfig.port.toString());

  // load from AsyncStorage
  const loadSettings = async () => {
    try {
      const savedHost = await AsyncStorage.getItem("serverHost");
      const savedPort = await AsyncStorage.getItem("serverPort");

      if (savedHost) {
        setServerConfig((prev) => ({ ...prev, host: savedHost }));
        setTempHost(savedHost);
      }
      if (savedPort) {
        const port = parseInt(savedPort);
        setServerConfig((prev) => ({ ...prev, port: port }));
        setTempPort(savedPort);
      }
    } catch (error) {
      console.error("Failed to load settings:", error);
    }
  };

  // saved to AsyncStorage
  const saveSettings = async () => {
    try {
      const port = parseInt(tempPort);
      if (isNaN(port) || port < 1 || port > 65535) {
        Alert.alert("Error", "Port number must between 1-65535");
        return;
      }

      if (!tempHost.trim()) {
        Alert.alert("Error", "Host cannot be empty");
        return;
      }

      await AsyncStorage.setItem("serverHost", tempHost);
      await AsyncStorage.setItem("serverPort", tempPort);

      setServerConfig({
        host: tempHost,
        port: port,
      });

      setShowSettings(false);
      Alert.alert("Success", "Settings saved successfully!");

      // if connected, reconnect with new settings
      if (client) {
        client.destroy();
        setIsConnected(false);
        setStatus("Settings updated, reconnecting...");
        setTimeout(() => {
          connectToServer();
        }, 1000);
      }
    } catch (error) {
      console.error("Failed to save settings:", error);
      Alert.alert("Error", "Failed to save settings: " + error.message);
    }
  };

  // Parse concatenated JSON messages
  const parseMessages = (data) => {
    try {
      // Split concatenated JSON objects
      const messages = data.split(/(?<=})\s*(?={)/);

      messages.forEach((msg) => {
        try {
          const parsed = JSON.parse(msg);
          handleMessage(parsed);
        } catch (e) {
          console.error("Failed to parse message:", e);
        }
      });
    } catch (e) {
      console.error("Failed to split messages:", e);
    }
  };

  // Handle different message types
  const handleMessage = (message) => {
    const { type, data, timestamp } = message;

    switch (type) {
      case "status":
        if (data.code === "200") {
          setIsConnected(true);
          setStatus("Connected successfully");
        }
        break;

      case "client":
        // Filter out own IP address
        const currentIP = client?.address?.address;
        const otherClients = data.filter((ip) => !ip.includes(currentIP));
        setConnectedClients(otherClients);
        break;

      case "msg":
        setReceivedMessages((prev) => [
          ...prev,
          {
            content: data,
            timestamp,
          },
        ]);
        break;
    }
  };

  const animatedStyles = useAnimatedStyle(() => {
    return {
      transform: [{ rotate: `${rotation.value}deg` }],
    };
  });

  const handleRefresh = () => {
    rotation.value = 0;
    console.log("disconnecting...");

    if (client) {
      client.destroy();
      setIsConnected(false);
      setStatus("Reconnecting...");
    }
    rotation.value = withRepeat(withTiming(360, { duration: 800 }), 1, false);
    connectToServer();
    console.log("reconnecting...");
  };

  const connectToServer = () => {
    // Close existing connection if any
    if (client) {
      client.destroy();
    }

    const newClient = TcpSocket.createConnection(serverConfig, () => {
      console.log("Connected to server");
      setStatus("Connecting to server...");
    });

    // data receive event
    newClient.on("data", (data) => {
      console.log("Received:", data.toString());
      parseMessages(data.toString());
    });

    newClient.on("error", (error) => {
      console.error("Connection Error:", error);
      setStatus("Connection Failed: " + error.message);
      setIsConnected(false);
    });

    newClient.on("close", () => {
      console.log("Connection Closed");
      setStatus("Connection Closed");
      setIsConnected(false);
      setConnectedClients([]);
    });

    setClient(newClient);
  };

  const sendMessage = () => {
    if (!client || !isConnected) {
      setStatus("Not Connected To Server");
      return;
    }

    try {
      client.write(message);
      setStatus("Message Sent");
      setMessage("");
    } catch (error) {
      setStatus("Failed to send message: " + error.message);
    }
  };

  useEffect(() => {
    loadSettings();
  }, []);

  useEffect(() => {
    connectToServer();
    return () => {
      if (client) {
        client.destroy();
      }
    };
  }, [serverConfig]);

  return (
    <View className="flex-1 p-6 bg-gray-50">
      <View className="items-center bg-gray-50">
        <View className="flex-row items-center justify-between w-full mb-4">
          <View className="w-6" />
          <Text className="text-3xl font-bold mt-4 mb-6">Popup Mobile</Text>
          <Pressable
            onPress={() => setShowSettings(true)}
            className="mt-4 mb-6 p-2"
            hitSlop={10}
          >
            <FontAwesome name="cog" size={24} color="#666" />
          </Pressable>
        </View>

        <Pressable onPress={connectToServer} className="mt-6 mb-4">
          <Entypo
            name="icloud"
            size={24}
            color={isConnected ? "green" : "red"}
          />
        </Pressable>
        <Text
          className={`mb-4 ${isConnected ? "text-green-600" : "text-red-600"}`}
        >
          {isConnected ? "Connected" : "Disconnected"}
        </Text>
        <Text className="text-xs text-gray-500 mb-6">
          {serverConfig.host}:{serverConfig.port}
        </Text>
      </View>

      <View className="relative flex-row mb-6">
        <TextInput
          className="flex-1 h-20 border border-gray-300 rounded-lg px-3 text-base"
          value={message}
          onChangeText={setMessage}
          placeholder="Type your popup message here"
        />
        {message.length > 0 && (
          <Pressable
            onPress={() => setMessage("")}
            className="absolute right-2 top-2 p-1"
            hitSlop={10}
          >
            <FontAwesome name="times-circle" size={20} color="#666" />
          </Pressable>
        )}
      </View>

      <Pressable
        onPress={sendMessage}
        android_ripple={{ color: "#ccc", borderless: false }}
        className={`py-3 px-4 rounded-lg ${
          isConnected ? "bg-blue-500 active:bg-blue-700" : "bg-gray-400"
        }`}
        disabled={!isConnected}
      >
        <Text className="text-white text-center text-lg">Send</Text>
      </Pressable>

      <Text className="mt-4 mb-6 text-blue-700">{status}</Text>

      {/* Connected Clients Section */}
      <View className="mb-4 border border-gray-300 rounded-lg p-3 h-24">
        <Text className="text-sm font-bold mb-2">Connected Clients:</Text>
        <ScrollView>
          {connectedClients.map((clientIP, index) => (
            <Text key={index} className="text-sm text-gray-600">
              {clientIP}
            </Text>
          ))}
          {connectedClients.length === 0 && (
            <Text className="text-sm text-gray-400 italic">
              No other clients connected
            </Text>
          )}
        </ScrollView>
      </View>

      {/* Messages Section */}
      <View className="border border-gray-300 rounded-lg p-3 h-32">
        <Text className="text-sm font-bold mb-2">Messages Received:</Text>
        <View className="flex-1">
          <ScrollView>
            {receivedMessages.map((msg, index) => (
              <Text key={index} className="text-sm text-gray-600">
                {msg.content}
                <Text className="text-xs text-gray-400">
                  {" "}
                  ({new Date(msg.timestamp).toLocaleTimeString()})
                </Text>
              </Text>
            ))}
          </ScrollView>
          {receivedMessages.length > 0 && (
            <Pressable
              onPress={() => setReceivedMessages([])}
              className="absolute right-2 top-2 p-1"
              hitSlop={10}
            >
              <FontAwesome6 name="trash-can" size={24} color="black" />
            </Pressable>
          )}
        </View>
      </View>

      <View className="items-center mt-5">
        <Pressable
          android_ripple={{ color: "#ccc", borderless: true }}
          className="bg-white-500"
          onPress={handleRefresh}
        >
          <Animated.View style={animatedStyles}>
            <FontAwesome name="refresh" size={80} color={"#000"} />
          </Animated.View>
        </Pressable>
      </View>

      {/* Settings Modal */}
      <Modal
        animationType="slide"
        transparent={true}
        visible={showSettings}
        onRequestClose={() => setShowSettings(false)}
      >
        <View className="flex-1 justify-center items-center bg-black bg-opacity-50">
          <View className="bg-white rounded-lg p-6 w-80 max-w-full">
            <Text className="text-xl font-bold mb-4 text-center">
              Server Settings
            </Text>

            <Text className="text-sm font-semibold mb-2">Host:</Text>
            <TextInput
              className="border border-gray-300 rounded-lg px-3 py-2 mb-4"
              value={tempHost}
              onChangeText={setTempHost}
              placeholder="192.168.1.100"
            />

            <Text className="text-sm font-semibold mb-2">Port:</Text>
            <TextInput
              className="border border-gray-300 rounded-lg px-3 py-2 mb-6"
              value={tempPort}
              onChangeText={setTempPort}
              placeholder="12345"
              keyboardType="numeric"
            />

            <View className="flex-row justify-between">
              <Pressable
                onPress={() => setShowSettings(false)}
                className="flex-1 bg-gray-300 rounded-lg py-3 px-4 mr-2"
              >
                <Text className="text-center text-gray-700">Cancel</Text>
              </Pressable>

              <Pressable
                onPress={saveSettings}
                className="flex-1 bg-blue-500 rounded-lg py-3 px-4 ml-2"
              >
                <Text className="text-center text-white">Save</Text>
              </Pressable>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}
