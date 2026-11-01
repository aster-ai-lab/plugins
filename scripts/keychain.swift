import Foundation
import CryptoKit
import Security

let roles: Set<String> = ["root", "targets", "snapshot", "timestamp"]
let arguments = CommandLine.arguments
func fail(_ message: String) -> Never { FileHandle.standardError.write(Data((message + "\n").utf8)); exit(1) }
guard arguments.count == 3, roles.contains(arguments[2]) else { fail("usage: keychain.swift ensure|sign|export-online ROLE") }
let operation = arguments[1]
let role = arguments[2]
let service = "dev.aster.plugins.tuf.v1"
let lookup: [String: Any] = [kSecClass as String: kSecClassGenericPassword,
    kSecAttrService as String: service, kSecAttrAccount as String: role,
    kSecReturnData as String: true, kSecMatchLimit as String: kSecMatchLimitOne]
var result: CFTypeRef?
let status = SecItemCopyMatching(lookup as CFDictionary, &result)
let key: Curve25519.Signing.PrivateKey
do {
    if status == errSecSuccess, let data = result as? Data {
        key = try Curve25519.Signing.PrivateKey(rawRepresentation: data)
    } else if status == errSecItemNotFound && operation == "ensure" {
        key = Curve25519.Signing.PrivateKey()
        let item: [String: Any] = [kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service, kSecAttrAccount as String: role,
            kSecAttrLabel as String: "Aster plugins TUF \(role)",
            kSecAttrSynchronizable as String: false, kSecValueData as String: key.rawRepresentation]
        let added = SecItemAdd(item as CFDictionary, nil)
        guard added == errSecSuccess else { fail("Keychain write failed: \(added)") }
    } else { fail("Keychain read failed: \(status)") }
    switch operation {
    case "ensure":
        let value = ["role": role, "public": key.publicKey.rawRepresentation.map { String(format: "%02x", $0) }.joined()]
        FileHandle.standardOutput.write(try JSONSerialization.data(withJSONObject: value, options: [.sortedKeys]))
    case "sign":
        var message = Data()
        while true {
            let chunk = try FileHandle.standardInput.read(upToCount: 64 * 1024) ?? Data()
            if chunk.isEmpty { break }
            guard message.count + chunk.count <= 8 * 1024 * 1024 else { fail("TUF metadata exceeds 8 MiB") }
            message.append(chunk)
        }
        let signature = try key.signature(for: message)
        print(signature.map { String(format: "%02x", $0) }.joined())
    case "export-online":
        guard role != "root" else { fail("Root key export is refused") }
        print(key.rawRepresentation.base64EncodedString())
    default: fail("Unknown Keychain operation")
    }
} catch { fail("Signing operation failed: \(error)") }
