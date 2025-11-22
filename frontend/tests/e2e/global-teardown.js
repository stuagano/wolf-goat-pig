
import { execSync } from 'child_process';
import path from 'path';

export default async () => {
  console.log('--- Running global teardown ---');
  const pythonScriptPath = path.join(__dirname, 'teardown.py');
  const backendDir = path.join(__dirname, '../../../backend');

  // Activate the virtual environment and run the teardown script
  const command = `cd ${backendDir} && source venv/bin/activate && python ${pythonScriptPath}`;
  
  try {
    console.log(`Executing command: ${command}`);
    execSync(command, { stdio: 'inherit' });
    console.log('--- Global teardown finished ---');
  } catch (error) {
    console.error('--- Global teardown failed ---', error);
    process.exit(1);
  }
};
