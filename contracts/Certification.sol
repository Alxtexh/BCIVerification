// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

contract Certification {
    struct Certificate {
        string registrationNo;      // Changed from Registration_No
        string candidateName;       // Changed from candidate_name
        string courseName;          // Changed from course_name
        string institution;         // Changed from Institution
        string ipfsHash;           // Changed from ipfs_hash
    }

    mapping(string => Certificate) public certificates;
    event CertificateGenerated(string certificate_id, string registrationNo, string candidateName, string courseName, string institution, string ipfsHash);
    event CertificateInvalidated(string certificate_id);

    function generateCertificate(
        string memory _certificate_id,
        string memory _registrationNo,    // Changed parameter name
        string memory _candidateName,     // Changed parameter name
        string memory _courseName,        // Changed parameter name
        string memory _institution,       // Changed parameter name
        string memory _ipfsHash          // Changed parameter name
    ) public {
        // Check if certificate with the given ID already exists
        require(
            bytes(certificates[_certificate_id].ipfsHash).length == 0,
            "Certificate with this ID already exists"
        );

        // Create the certificate
        Certificate memory cert = Certificate({
            registrationNo: _registrationNo,
            candidateName: _candidateName,
            courseName: _courseName,
            institution: _institution,
            ipfsHash: _ipfsHash
        });

        // Store the certificate in the mapping
        certificates[_certificate_id] = cert;

        // Emit an event with detailed information
        emit CertificateGenerated(_certificate_id, _registrationNo, _candidateName, _courseName, _institution, _ipfsHash);
    }

    function getCertificate(string memory certificateId) public view returns (
        string memory registrationNo,
        string memory candidateName,
        string memory courseName,
        string memory institution,
        string memory ipfsHash
    ) {
        require(bytes(certificates[certificateId].registrationNo).length > 0, "Certificate with this ID does not exist");
        Certificate memory cert = certificates[certificateId];
        return (
            cert.registrationNo,
            cert.candidateName,
            cert.courseName,
            cert.institution,
            cert.ipfsHash
        );
    }

    function isVerified(
        string memory _certificate_id
    ) public view returns (bool) {
        return bytes(certificates[_certificate_id].ipfsHash).length != 0;
    }

    function invalidateCertificate(string memory _certificate_id) public {
        // Check if the certificate with the given ID exists
        require(
            bytes(certificates[_certificate_id].ipfsHash).length != 0,
            "Certificate with this ID does not exist"
        );

        // Invalidate the certificate
        delete certificates[_certificate_id];

        // Emit an event
        emit CertificateInvalidated(_certificate_id);
    }

    function certificateExists(string memory certificateId) public view returns (bool) {
        return bytes(certificates[certificateId].registrationNo).length > 0;
    }
}
