const fs = require('fs');
const path = require('path');
const solc = require('solc');

const contractPath = path.resolve(__dirname, 'contracts', 'FaceVerificationRegistry.sol');
const source = fs.readFileSync(contractPath, 'utf8');

const input = {
  language: 'Solidity',
  sources: {
    'FaceVerificationRegistry.sol': {
      content: source,
    },
  },
  settings: {
    optimizer: {
      enabled: true,
      runs: 200,
    },
    outputSelection: {
      '*': {
        '*': ['abi', 'evm.bytecode.object'],
      },
    },
  },
};

console.log('Compiling FaceVerificationRegistry.sol with Solc 0.8.20...');
const output = JSON.parse(solc.compile(JSON.stringify(input)));

if (output.errors) {
  let hasError = false;
  output.errors.forEach(err => {
    console.error(err.formattedMessage);
    if (err.severity === 'error') hasError = true;
  });
  if (hasError) {
    process.exit(1);
  }
}

const contract = output.contracts['FaceVerificationRegistry.sol']['FaceVerificationRegistry'];
const compiledData = {
  contractName: 'FaceVerificationRegistry',
  abi: contract.abi,
  bytecode: contract.evm.bytecode.object,
};

const outputPath = path.resolve(__dirname, 'contracts', 'compiled_contract.json');
fs.writeFileSync(outputPath, JSON.stringify(compiledData, null, 2));
console.log(`Compilation successful! Saved to: ${outputPath}`);
