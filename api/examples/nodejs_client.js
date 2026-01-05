/**
 * JavaScript/Node.js client example for the Protein Disorder Classification API.
 * 
 * Install dependencies:
 *   npm install axios
 * 
 * Usage:
 *   node nodejs_client.js
 */

const axios = require('axios');

/**
 * Client for the Protein Disorder Classification API
 */
class ProteinClassifierClient {
  /**
   * Initialize the client
   * @param {string} baseUrl - Base URL of the API (default: http://localhost:8000)
   * @param {string} apiKey - API key for authentication
   */
  constructor(baseUrl = 'http://localhost:8000', apiKey = null) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.apiKey = apiKey;
    
    this.client = axios.create({
      baseURL: this.baseUrl,
      headers: apiKey ? { 'X-API-Key': apiKey } : {}
    });
  }

  /**
   * Check if the API is healthy
   * @returns {Promise<Object>} Health status
   */
  async healthCheck() {
    const response = await this.client.get('/health');
    return response.data;
  }

  /**
   * Classify protein sequences
   * @param {Array<{id: string, sequence: string}>} sequences - Sequences to classify
   * @param {number} threshold - Classification threshold (default: 5)
   * @returns {Promise<Object>} Classification results
   */
  async classify(sequences, threshold = 5) {
    const response = await this.client.post('/api/v1/classify', {
      sequences: sequences,
      threshold: threshold
    });
    return response.data;
  }

  /**
   * Classify sequences from FASTA format
   * @param {string} fastaText - FASTA formatted text
   * @param {number} threshold - Classification threshold (default: 5)
   * @returns {Promise<Object>} Classification results
   */
  async classifyFasta(fastaText, threshold = 5) {
    const response = await this.client.post(
      `/api/v1/classify/fasta?threshold=${threshold}`,
      fastaText,
      {
        headers: { 'Content-Type': 'text/plain' }
      }
    );
    return response.data;
  }
}

/**
 * Example usage
 */
async function main() {
  // Initialize client with API key
  const apiKey = 'YOUR_API_KEY_HERE';  // Replace with your API key
  const client = new ProteinClassifierClient('http://localhost:8000', apiKey);

  try {
    // Check API health
    console.log('Checking API health...');
    const health = await client.healthCheck();
    console.log(`API Status: ${health.status}`);
    console.log(`API Version: ${health.version}`);
    console.log();

    // Example 1: Classify a single sequence
    console.log('='.repeat(60));
    console.log('Example 1: Single Sequence Classification');
    console.log('='.repeat(60));

    let results = await client.classify([
      { id: 'albumin_fragment', sequence: 'MKVLWAASLLLLASAARA' }
    ]);

    for (const result of results.results) {
      console.log(`\nSequence ID: ${result.id}`);
      console.log(`Classification: ${result.classification}`);
      console.log(`Confidence: ${result.confidence}`);
      console.log(`Conditions Met: ${result.conditions_met}/${result.threshold}`);
      console.log(`Processing Time: ${result.processing_time_ms}ms`);
      console.log(`\nFeatures:`);
      for (const [feature, value] of Object.entries(result.features)) {
        console.log(`  ${feature}: ${value.toFixed(4)}`);
      }
    }
    console.log();

    // Example 2: Classify multiple sequences
    console.log('='.repeat(60));
    console.log('Example 2: Batch Classification');
    console.log('='.repeat(60));

    results = await client.classify([
      { id: 'structured_protein', sequence: 'ILVILVILVILVILVILVILVIL' },
      { id: 'disordered_protein', sequence: 'KKEEKKEEKKEEKKEEGGPPGGPP' },
      { id: 'mixed_protein', sequence: 'ACDEFGHIKLMNPQRSTVWY' }
    ]);

    console.log(`\nProcessed ${results.total_sequences} sequences in ${results.total_time_ms.toFixed(2)}ms`);
    console.log();

    for (const result of results.results) {
      const id = result.id.padEnd(25);
      const classification = result.classification.padEnd(12);
      console.log(`${id} -> ${classification} (confidence: ${result.confidence.toFixed(2)}, ` +
                  `conditions: ${result.conditions_met}/${result.threshold})`);
    }
    console.log();

    // Example 3: Classify from FASTA
    console.log('='.repeat(60));
    console.log('Example 3: FASTA Classification');
    console.log('='.repeat(60));

    const fastaText = `>protein1
MKVLWAASLLLLASAARA
>protein2
MALWMRLLPLLALLALWGPDPAAAF
`;

    results = await client.classifyFasta(fastaText);

    console.log(`\nProcessed ${results.total_sequences} sequences from FASTA`);
    console.log();

    for (const result of results.results) {
      const id = result.id.padEnd(15);
      console.log(`${id} -> ${result.classification}`);
    }

  } catch (error) {
    if (error.response) {
      console.error('API Error:', error.response.status, error.response.data);
    } else {
      console.error('Error:', error.message);
    }
  }
}

// Run the example
if (require.main === module) {
  main();
}

module.exports = { ProteinClassifierClient };
