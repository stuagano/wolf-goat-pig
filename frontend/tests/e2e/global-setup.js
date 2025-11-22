import { execSync } from 'child_process';
import path from 'path';

export default async () => {
  console.log('--- Running global setup ---');
  const pythonScriptPath = path.join(__dirname, 'setup.py');
  const backendDir = path.join(__dirname, '../../../backend');

  // Activate the virtual environment and run the setup script
  const command = `cd ${backendDir} && source venv/bin/activate && python ${pythonScriptPath}`;
  
  try {
    console.log(`Executing command: ${command}`);
    execSync(command, { stdio: 'inherit' });
    console.log('--- Global setup finished ---');
  } catch (error) {
    console.error('--- Global setup failed ---', error);
    process.exit(1);
  }
};