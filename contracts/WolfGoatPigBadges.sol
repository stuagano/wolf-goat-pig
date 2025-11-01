// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Strings.sol";

/**
 * @title WolfGoatPigBadges
 * @dev ERC-1155 NFT contract for Wolf Goat Pig achievement badges
 *
 * Features:
 * - Multi-token support (ERC-1155) for gas-efficient badge minting
 * - Supply caps per badge type
 * - Metadata URIs stored on IPFS
 * - Only owner (backend API) can mint badges
 * - Badges are soulbound (non-transferable) by default
 */
contract WolfGoatPigBadges is ERC1155, Ownable {
    using Strings for uint256;

    // Badge metadata
    struct Badge {
        string name;
        string rarity; // common, rare, epic, legendary, mythic
        uint256 maxSupply;
        uint256 currentSupply;
        bool isActive;
        bool isSoulbound; // Non-transferable
    }

    // Mapping from badge ID to Badge data
    mapping(uint256 => Badge) public badges;

    // Mapping from badge ID to metadata URI (IPFS hash)
    mapping(uint256 => string) private _badgeURIs;

    // Base URI for all badges (IPFS gateway)
    string private _baseURI;

    // Events
    event BadgeCreated(uint256 indexed badgeId, string name, string rarity, uint256 maxSupply);
    event BadgeMinted(address indexed to, uint256 indexed badgeId, uint256 serialNumber);
    event BadgeURIUpdated(uint256 indexed badgeId, string newURI);
    event BaseURIUpdated(string newBaseURI);

    constructor(string memory baseURI_) ERC1155("") Ownable(msg.sender) {
        _baseURI = baseURI_;
    }

    /**
     * @dev Create a new badge type
     * @param badgeId Unique identifier for the badge
     * @param name Badge name
     * @param rarity Badge rarity tier
     * @param maxSupply Maximum number that can be minted (0 = unlimited)
     * @param isSoulbound Whether badge is non-transferable
     * @param metadataURI IPFS URI for badge metadata
     */
    function createBadge(
        uint256 badgeId,
        string memory name,
        string memory rarity,
        uint256 maxSupply,
        bool isSoulbound,
        string memory metadataURI
    ) external onlyOwner {
        require(badges[badgeId].maxSupply == 0, "Badge already exists");

        badges[badgeId] = Badge({
            name: name,
            rarity: rarity,
            maxSupply: maxSupply,
            currentSupply: 0,
            isActive: true,
            isSoulbound: isSoulbound
        });

        _badgeURIs[badgeId] = metadataURI;

        emit BadgeCreated(badgeId, name, rarity, maxSupply);
    }

    /**
     * @dev Mint a badge to a player
     * @param to Player's wallet address
     * @param badgeId Badge to mint
     */
    function mintBadge(address to, uint256 badgeId) external onlyOwner {
        Badge storage badge = badges[badgeId];

        require(badge.isActive, "Badge is not active");
        require(badge.maxSupply == 0 || badge.currentSupply < badge.maxSupply, "Max supply reached");
        require(balanceOf(to, badgeId) == 0, "Player already has this badge");

        badge.currentSupply++;
        uint256 serialNumber = badge.currentSupply;

        _mint(to, badgeId, 1, "");

        emit BadgeMinted(to, badgeId, serialNumber);
    }

    /**
     * @dev Batch mint multiple badges to a player
     * @param to Player's wallet address
     * @param badgeIds Array of badge IDs to mint
     */
    function mintBadgeBatch(address to, uint256[] memory badgeIds) external onlyOwner {
        uint256[] memory amounts = new uint256[](badgeIds.length);

        for (uint256 i = 0; i < badgeIds.length; i++) {
            Badge storage badge = badges[badgeIds[i]];

            require(badge.isActive, "Badge is not active");
            require(badge.maxSupply == 0 || badge.currentSupply < badge.maxSupply, "Max supply reached");
            require(balanceOf(to, badgeIds[i]) == 0, "Player already has this badge");

            badge.currentSupply++;
            amounts[i] = 1;

            emit BadgeMinted(to, badgeIds[i], badge.currentSupply);
        }

        _mintBatch(to, badgeIds, amounts, "");
    }

    /**
     * @dev Get badge information
     * @param badgeId Badge ID to query
     */
    function getBadge(uint256 badgeId) external view returns (
        string memory name,
        string memory rarity,
        uint256 maxSupply,
        uint256 currentSupply,
        bool isActive,
        bool isSoulbound
    ) {
        Badge memory badge = badges[badgeId];
        return (
            badge.name,
            badge.rarity,
            badge.maxSupply,
            badge.currentSupply,
            badge.isActive,
            badge.isSoulbound
        );
    }

    /**
     * @dev Get all badges owned by an address
     * @param owner Address to query
     * @param badgeIds Array of badge IDs to check
     */
    function getBadgesOfOwner(address owner, uint256[] memory badgeIds)
        external
        view
        returns (uint256[] memory)
    {
        uint256[] memory ownedBadges = new uint256[](badgeIds.length);
        uint256 count = 0;

        for (uint256 i = 0; i < badgeIds.length; i++) {
            if (balanceOf(owner, badgeIds[i]) > 0) {
                ownedBadges[count] = badgeIds[i];
                count++;
            }
        }

        // Resize array to actual count
        uint256[] memory result = new uint256[](count);
        for (uint256 i = 0; i < count; i++) {
            result[i] = ownedBadges[i];
        }

        return result;
    }

    /**
     * @dev Update badge metadata URI
     * @param badgeId Badge ID to update
     * @param newURI New IPFS URI
     */
    function setBadgeURI(uint256 badgeId, string memory newURI) external onlyOwner {
        _badgeURIs[badgeId] = newURI;
        emit BadgeURIUpdated(badgeId, newURI);
    }

    /**
     * @dev Update base URI for all badges
     * @param newBaseURI New base URI (IPFS gateway)
     */
    function setBaseURI(string memory newBaseURI) external onlyOwner {
        _baseURI = newBaseURI;
        emit BaseURIUpdated(newBaseURI);
    }

    /**
     * @dev Toggle badge active status
     * @param badgeId Badge ID to toggle
     * @param isActive New active status
     */
    function setBadgeActive(uint256 badgeId, bool isActive) external onlyOwner {
        badges[badgeId].isActive = isActive;
    }

    /**
     * @dev Get URI for a specific badge
     * @param badgeId Badge ID to query
     */
    function uri(uint256 badgeId) public view override returns (string memory) {
        string memory badgeURI = _badgeURIs[badgeId];

        if (bytes(badgeURI).length > 0) {
            return string(abi.encodePacked(_baseURI, badgeURI));
        }

        return string(abi.encodePacked(_baseURI, badgeId.toString(), ".json"));
    }

    /**
     * @dev Override transfer functions to enforce soulbound badges
     * Soulbound badges cannot be transferred
     */
    function safeTransferFrom(
        address from,
        address to,
        uint256 id,
        uint256 amount,
        bytes memory data
    ) public override {
        require(!badges[id].isSoulbound, "Badge is soulbound and cannot be transferred");
        super.safeTransferFrom(from, to, id, amount, data);
    }

    function safeBatchTransferFrom(
        address from,
        address to,
        uint256[] memory ids,
        uint256[] memory amounts,
        bytes memory data
    ) public override {
        for (uint256 i = 0; i < ids.length; i++) {
            require(!badges[ids[i]].isSoulbound, "Badge is soulbound and cannot be transferred");
        }
        super.safeBatchTransferFrom(from, to, ids, amounts, data);
    }

    /**
     * @dev Check if contract supports an interface
     */
    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC1155)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}
