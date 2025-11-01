const hre = require("hardhat");

async function main() {
  console.log("🚀 Deploying Wolf Goat Pig Badges NFT Contract...\n");

  // Get the deployer account
  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying with account:", deployer.address);

  const balance = await hre.ethers.provider.getBalance(deployer.address);
  console.log("Account balance:", hre.ethers.formatEther(balance), "ETH\n");

  // Base URI for IPFS metadata
  // You can use:
  // - Public IPFS gateway: https://ipfs.io/ipfs/
  // - Pinata gateway: https://gateway.pinata.cloud/ipfs/
  // - Your own IPFS node
  const baseURI = process.env.BASE_URI || "https://ipfs.io/ipfs/";

  console.log("Base URI:", baseURI);

  // Deploy the contract
  const WolfGoatPigBadges = await hre.ethers.getContractFactory("WolfGoatPigBadges");
  const badges = await WolfGoatPigBadges.deploy(baseURI);

  await badges.waitForDeployment();

  const contractAddress = await badges.getAddress();
  console.log("\n✅ WolfGoatPigBadges deployed to:", contractAddress);

  // Wait for a few block confirmations
  console.log("\n⏳ Waiting for block confirmations...");
  await badges.deploymentTransaction().wait(5);

  console.log("\n📝 Deployment Summary:");
  console.log("==========================================");
  console.log("Contract Address:", contractAddress);
  console.log("Deployer:", deployer.address);
  console.log("Network:", hre.network.name);
  console.log("Base URI:", baseURI);
  console.log("==========================================\n");

  // Verify on block explorer
  if (hre.network.name !== "hardhat" && hre.network.name !== "localhost") {
    console.log("🔍 Verifying contract on block explorer...");
    try {
      await hre.run("verify:verify", {
        address: contractAddress,
        constructorArguments: [baseURI],
      });
      console.log("✅ Contract verified successfully!");
    } catch (error) {
      console.log("❌ Verification failed:", error.message);
      console.log("You can verify manually using:");
      console.log(`npx hardhat verify --network ${hre.network.name} ${contractAddress} "${baseURI}"`);
    }
  }

  // Save deployment info
  const fs = require("fs");
  const deploymentInfo = {
    network: hre.network.name,
    contractAddress: contractAddress,
    deployer: deployer.address,
    baseURI: baseURI,
    deployedAt: new Date().toISOString(),
    blockNumber: await hre.ethers.provider.getBlockNumber(),
  };

  const outputPath = `./deployments/${hre.network.name}.json`;
  fs.mkdirSync("./deployments", { recursive: true });
  fs.writeFileSync(outputPath, JSON.stringify(deploymentInfo, null, 2));
  console.log(`\n📄 Deployment info saved to: ${outputPath}`);

  console.log("\n🎉 Deployment complete!");
  console.log("\n🔗 Next steps:");
  console.log("1. Update backend .env with CONTRACT_ADDRESS:", contractAddress);
  console.log("2. Create badge metadata files and upload to IPFS");
  console.log("3. Run badge seed script to create badges on-chain");
  console.log("4. Test minting a badge to your wallet\n");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
