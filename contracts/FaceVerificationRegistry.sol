// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title FaceVerificationRegistry
 * @dev Immutable on-chain registry for face scan discoveries and social media match evidence.
 * Provides verifiable proof of existence, timestamping, and tamper detection.
 */
contract FaceVerificationRegistry {
    
    struct VerificationRecord {
        bytes32 evidenceHash;     // Root cryptographic fingerprint of the discovery
        bytes32 faceHash;         // SHA-256 hash of the normalized face crop
        bytes32 mediaHash;        // SHA-256 hash of the matched social media image/content
        string sourceUrl;         // Genuine live social post URL
        string platform;          // Platform name (e.g., Twitter/X, Reddit, GitHub, Web)
        uint256 timestamp;        // Block timestamp when registered
        address verifier;         // Account that executed and attested the verification
        bool exists;              // State flag
    }

    // Mapping from evidenceHash to VerificationRecord
    mapping(bytes32 => VerificationRecord) private _records;
    
    // Ordered list of all registered evidence hashes
    bytes32[] private _evidenceList;

    // Events
    event FaceMatchVerified(
        bytes32 indexed evidenceHash,
        bytes32 indexed faceHash,
        string platform,
        string sourceUrl,
        uint256 timestamp,
        address verifiedBy
    );

    /**
     * @notice Registers a new face-to-content discovery record on-chain using deterministic evidenceHash.
     */
    function recordVerification(
        bytes32 evidenceHash,
        bytes32 faceHash,
        bytes32 mediaHash,
        string calldata sourceUrl,
        string calldata platform
    ) external returns (bytes32) {
        require(evidenceHash != bytes32(0), "Invalid evidence hash");
        require(faceHash != bytes32(0), "Invalid face hash");
        require(mediaHash != bytes32(0), "Invalid media hash");
        require(bytes(sourceUrl).length > 0, "Source URL cannot be empty");
        require(!_records[evidenceHash].exists, "Record already exists");

        VerificationRecord memory record = VerificationRecord({
            evidenceHash: evidenceHash,
            faceHash: faceHash,
            mediaHash: mediaHash,
            sourceUrl: sourceUrl,
            platform: platform,
            timestamp: block.timestamp,
            verifier: msg.sender,
            exists: true
        });

        _records[evidenceHash] = record;
        _evidenceList.push(evidenceHash);

        emit FaceMatchVerified(
            evidenceHash,
            faceHash,
            platform,
            sourceUrl,
            block.timestamp,
            msg.sender
        );

        return evidenceHash;
    }

    /**
     * @notice Retrieves the full verification record by evidence hash.
     */
    function getRecord(bytes32 evidenceHash)
        external
        view
        returns (
            bytes32 faceHash,
            bytes32 mediaHash,
            string memory sourceUrl,
            string memory platform,
            uint256 timestamp,
            address verifier,
            bool exists
        )
    {
        VerificationRecord storage rec = _records[evidenceHash];
        require(rec.exists, "Record does not exist");
        return (
            rec.faceHash,
            rec.mediaHash,
            rec.sourceUrl,
            rec.platform,
            rec.timestamp,
            rec.verifier,
            rec.exists
        );
    }

    /**
     * @notice Re-verifies live content against the immutable on-chain record.
     */
    function verifyIntegrity(bytes32 evidenceHash, bytes32 currentMediaHash)
        external
        view
        returns (bool isValid)
    {
        VerificationRecord storage rec = _records[evidenceHash];
        if (!rec.exists) {
            return false;
        }
        return (rec.mediaHash == currentMediaHash);
    }

    /**
     * @notice Returns total number of registered verifications.
     */
    function getTotalRecords() external view returns (uint256) {
        return _evidenceList.length;
    }
}
