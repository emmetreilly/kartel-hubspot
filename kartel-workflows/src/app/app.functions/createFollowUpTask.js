const hubspot = require('@hubspot/api-client');

exports.main = async (context = {}) => {
  const { hs_object_id, hubspot_owner_id } = context.propertiesToSend;

  const hubspotClient = new hubspot.Client({
    accessToken: process.env.PRIVATE_APP_ACCESS_TOKEN
  });

  try {
    // Get the original deal to find the associated company
    const originalDeal = await hubspotClient.crm.deals.basicApi.getById(
      hs_object_id,
      ['dealname'],
      undefined,
      ['companies']
    );

    // Get associated company name
    const companyAssociations = originalDeal.associations?.companies?.results || [];
    let companyName = 'Unknown Company';

    if (companyAssociations.length > 0) {
      const company = await hubspotClient.crm.companies.basicApi.getById(
        companyAssociations[0].id,
        ['name']
      );
      companyName = company.properties.name || 'Unknown Company';
    }

    // Create a follow-up task (lighter touch - no deal created)
    await hubspotClient.crm.objects.basicApi.create('tasks', {
      properties: {
        hs_task_subject: `Final follow-up: ${companyName} - no response, one more try`,
        hs_task_body: `Original deal: ${originalDeal.properties.dealname}\n\nThis contact went dark. One final attempt before moving on.`,
        hs_task_status: 'NOT_STARTED',
        hs_task_priority: 'LOW',
        hubspot_owner_id: hubspot_owner_id,
        hs_timestamp: Date.now()
      }
    });

    return {
      outputFields: {
        status: 'success',
        company_name: companyName
      }
    };
  } catch (error) {
    return {
      outputFields: {
        status: 'error',
        message: error.message
      }
    };
  }
};
