package com.popup.android.crypto

import android.util.Base64
import java.security.KeyPair
import java.security.KeyPairGenerator
import java.security.PrivateKey
import java.security.PublicKey
import javax.crypto.Cipher
import javax.crypto.spec.IvParameterSpec
import javax.crypto.spec.SecretKeySpec

/**
 * Handles RSA-2048 key exchange and AES-256-CBC message encryption.
 * All functions are stateless — keys are managed by the ViewModel.
 *
 * Protocol (must match server + other clients):
 * - RSA: 2048-bit, PKCS#1 v1.5 padding
 * - AES: 256-bit key, CBC mode, PKCS5Padding (= PKCS7 for 16-byte blocks)
 * - Message format: base64(random_16_byte_IV + AES_CBC_ciphertext)
 * - AES key transported as 64-char hex string, RSA-encrypted
 */
object CryptoManager {

    // ── RSA ──────────────────────────────────────────────

    /** Generate a fresh RSA-2048 key pair */
    fun generateRsaKeyPair(): KeyPair {
        val generator = KeyPairGenerator.getInstance("RSA")
        generator.initialize(2048)
        return generator.generateKeyPair()
    }

    /** Serialize RSA public key to PEM format (server expects this) */
    fun getPublicKeyPem(publicKey: PublicKey): String {
        val encoded = Base64.encodeToString(publicKey.encoded, Base64.NO_WRAP)
        return buildString {
            appendLine("-----BEGIN PUBLIC KEY-----")
            // PEM wraps at 64 characters per line
            encoded.chunked(64).forEach { appendLine(it) }
            appendLine("-----END PUBLIC KEY-----")
        }
    }

    /**
     * RSA-decrypt the server's response to recover the AES key.
     * Server encrypts the hex-encoded AES key with our public key.
     * Returns the raw hex string (e.g. "a1b2c3...").
     */
    fun rsaDecrypt(privateKey: PrivateKey, encryptedBase64: String): String {
        val cipher = Cipher.getInstance("RSA/ECB/PKCS1Padding")
        cipher.init(Cipher.DECRYPT_MODE, privateKey)
        val encryptedBytes = Base64.decode(encryptedBase64, Base64.DEFAULT)
        val decrypted = cipher.doFinal(encryptedBytes)
        return String(decrypted, Charsets.UTF_8)
    }

    /** Parse hex string (from server) into AES key bytes */
    fun hexToBytes(hex: String): ByteArray {
        return ByteArray(hex.length / 2) { i ->
            hex.substring(i * 2, i * 2 + 2).toInt(16).toByte()
        }
    }

    // ── AES ──────────────────────────────────────────────

    /** Encrypt plaintext → base64(IV + ciphertext) */
    fun aesEncrypt(aesKey: ByteArray, plaintext: String): String {
        val iv = ByteArray(16).also { java.security.SecureRandom().nextBytes(it) }
        val cipher = Cipher.getInstance("AES/CBC/PKCS5Padding")
        cipher.init(Cipher.ENCRYPT_MODE, SecretKeySpec(aesKey, "AES"), IvParameterSpec(iv))
        val ciphertext = cipher.doFinal(plaintext.toByteArray(Charsets.UTF_8))
        return Base64.encodeToString(iv + ciphertext, Base64.NO_WRAP)
    }

    /**
     * Decrypt base64(IV + ciphertext) → plaintext.
     * Tries currentKey first; if that fails and previousKey is provided,
     * retries with previousKey (handles key rotation window).
     */
    fun aesDecrypt(
        currentKey: ByteArray,
        previousKey: ByteArray?,
        encryptedBase64: String
    ): String {
        val raw = Base64.decode(encryptedBase64, Base64.DEFAULT)
        val iv = raw.copyOfRange(0, 16)
        val ciphertext = raw.copyOfRange(16, raw.size)

        return try {
            doAesDecrypt(currentKey, iv, ciphertext)
        } catch (e: Exception) {
            if (previousKey != null) {
                doAesDecrypt(previousKey, iv, ciphertext)
            } else {
                throw e
            }
        }
    }

    private fun doAesDecrypt(key: ByteArray, iv: ByteArray, ciphertext: ByteArray): String {
        val cipher = Cipher.getInstance("AES/CBC/PKCS5Padding")
        cipher.init(Cipher.DECRYPT_MODE, SecretKeySpec(key, "AES"), IvParameterSpec(iv))
        val plaintext = cipher.doFinal(ciphertext)
        return String(plaintext, Charsets.UTF_8)
    }
}
