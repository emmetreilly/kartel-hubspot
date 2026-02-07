const hubspot = require('@hubspot/api-client');

exports.main = async (context = {}) => {
  const { hs_object_id, loss_reason, hubspot_owner_id } = context.propertiesToSend;

  const hubspotClient = new hubspot.Client({
    accessToken: process.env.PRIVATE_APP_ACCESS_TOKEN
  });

  try {
    // Get the original deal to find the associated company
    const originalDeal = await hubspotClient.crm.deals.basicApi.getById(
      hs_object_id,
      ['dealname', 'hubspot_owner_id'],
      undefined,
      ['companies']
    );

    // Get associated company
    const companyAssociations = originalDeal.associations?.companies?.results || [];
    if (companyAssociations.length === 0) {
      return {
        outputFields: {
          status: 'error',
          message: 'No company associated with this deal'
        }
      };
    }

    const companyId = companyAssociations[0].id;

    // Get company name for the deal name
    const company = await hubspotClient.crm.companies.basicApi.getById(companyId, ['name']);
    const companyName = company.properties.name || 'Unknown Company';

    // Create the re-engagement deal
    const reengagementDeal = await hubspotClient.crm.deals.basicApi.create({
      properties: {
        dealname: `Re-engage: ${companyName}`,
        pipeline: '1880222400', // Re-engagement Pipeline
        dealstage: '2978916037', // Opportunity Identified
        hubspot_owner_id: hubspot_owner_id || originalDeal.properties.hubspot_owner_id,
        loss_reason_original: loss_reason
      }
    });

    // Associate with company (not contacts from old deal)
    await hubspotClient.crm.deals.associationsApi.create(
      reengagementDeal.id,
      'companies',
      companyId,
      [{ associationCategory: 'HUBSPOT_DEFINED', associationTypeId: 342 }]
    );

    // Create a task for the owner
    const reasonText = {
      'budget_timing': 'lost 90 days ago due to budget/timing',
      'competitor': 'lost to competitor 6 months ago'
    }[loss_reason] || 'ready for re-engagement';

    await hubspotClient.crm.objects.basicApi.create('tasks', {
      properties: {
        hs_task_subject: `Re-engage ${companyName} - ${reasonText}`,
        hs_task_body: `Original deal: ${originalDeal.properties.dealname}\nReason for loss: ${loss_reason}`,
        hs_task_status: 'NOT_STARTED',
        hs_task_priority: 'MEDIUM',
        hubspot_owner_id: hubspot_owner_id || originalDeal.properties.hubspot_owner_id,
        hs_timestamp: Date.now()
      }
    });

    return {
      outputFields: {
        status: 'success',
        reengagement_deal_id: reengagementDeal.id,
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
